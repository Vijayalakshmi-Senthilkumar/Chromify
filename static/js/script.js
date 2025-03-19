document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const dropArea = document.getElementById('dropArea');
    const fileInput = document.getElementById('fileInput');
    const previewContainer = document.getElementById('previewContainer');
    const originalPreview = document.getElementById('originalPreview');
    const colorizedPreview = document.getElementById('colorizedPreview');
    const imageControls = document.getElementById('imageControls');
    const actionButtons = document.getElementById('actionButtons');
    const loadingOriginal = document.getElementById('loadingOriginal');
    const loadingColorized = document.getElementById('loadingColorized');
    const downloadBtn = document.getElementById('downloadBtn');
    const shareBtn = document.getElementById('shareBtn');
    const resetBtn = document.getElementById('resetBtn');
    const brightnessSlider = document.getElementById('brightness');
    const contrastSlider = document.getElementById('contrast');
    const saturationSlider = document.getElementById('saturation');
    
    // Store file paths for cleanup and session info
    let filePaths = [];
    let sessionId = '';
    
    // Try to get session ID from localStorage if exists
    const storedSession = localStorage.getItem('chromifySessionId');
    if (storedSession) {
        sessionId = storedSession;
    }
    
    // Register files with server to ensure they're tracked
    function registerFilesWithSession() {
        if (filePaths.length > 0 && sessionId) {
            // Store session ID for future use
            localStorage.setItem('chromifySessionId', sessionId);
            
            console.log('Session ID stored:', sessionId);
            console.log('Files registered:', filePaths);
        }
    }
    
    // Drag & Drop Events
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('dragging');
    }
    
    function unhighlight() {
        dropArea.classList.remove('dragging');
    }
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    }
    
    // Handle file selection via button
    dropArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    fileInput.addEventListener('change', function() {
        handleFiles(this.files);
    });
    
    function handleFiles(files) {
        if (files.length > 0) {
            const file = files[0];
            if (!file.type.match('image.*')) {
                alert('Please select an image file');
                return;
            }
            
            // Show preview container
            previewContainer.style.display = 'flex';
            
            // Show loading indicators
            loadingOriginal.classList.add('active');
            loadingColorized.classList.add('active');
            
            // Display original image
            const reader = new FileReader();
            reader.onload = function(e) {
                originalPreview.src = e.target.result;
                originalPreview.onload = function() {
                    // Hide loading indicator for original
                    loadingOriginal.classList.remove('active');
                };
            };
            reader.readAsDataURL(file);
            
            // Send to server for colorization
            const formData = new FormData();
            formData.append('image', file);
            
            fetch('/api/colorize', {
                method: 'POST',
                body: formData
            })
            .then(response => {
                if (!response.ok) {
                    return response.json().then(err => { throw new Error(err.error || 'Server error'); });
                }
                return response.json();
            })
            .then(data => {
                // Store file paths for later cleanup
                filePaths = [data.original, data.colorized];
                
                // Store session ID
                if (data.session_id) {
                    sessionId = data.session_id;
                    registerFilesWithSession();
                }
                
                // Display colorized image
                colorizedPreview.src = data.colorized + '?t=' + new Date().getTime(); // Prevent caching
                colorizedPreview.onload = function() {
                    // Hide loading indicator for colorized
                    loadingColorized.classList.remove('active');
                    
                    // Show controls and buttons
                    imageControls.style.display = 'flex';
                    actionButtons.style.display = 'flex';
                };
            })
            .catch(error => {
                alert('Error colorizing image: ' + error.message);
                loadingColorized.classList.remove('active');
            });
        }
    }
    
    // Handle image adjustments
    brightnessSlider.addEventListener('input', updateFilters);
    contrastSlider.addEventListener('input', updateFilters);
    saturationSlider.addEventListener('input', updateFilters);
    
    function updateFilters() {
        const brightness = brightnessSlider.value;
        const contrast = contrastSlider.value;
        const saturation = saturationSlider.value;
        
        colorizedPreview.style.filter = `brightness(${brightness}%) contrast(${contrast}%) saturate(${saturation}%)`;
    }
    
    // Download button
    downloadBtn.addEventListener('click', function() {
        if (colorizedPreview.src) {
            // Create temporary link with filtered image
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            
            // Set canvas dimensions to match image
            canvas.width = colorizedPreview.naturalWidth;
            canvas.height = colorizedPreview.naturalHeight;
            
            // Draw image with filters applied
            ctx.filter = colorizedPreview.style.filter;
            ctx.drawImage(colorizedPreview, 0, 0);
            
            // Create download link
            const link = document.createElement('a');
            link.download = 'chromify-colorized.jpg';
            link.href = canvas.toDataURL('image/jpeg', 0.9);
            link.click();
        }
    });
    
    // Share button (simplified for demo)
    shareBtn.addEventListener('click', function() {
        if (navigator.share) {
            navigator.share({
                title: 'My Colorized Image',
                text: 'Check out this image I colorized with Chromify!',
                url: window.location.href
            })
            .catch(error => console.log('Error sharing:', error));
        } else {
            alert('Sharing is not supported in your browser. You can download the image and share it manually.');
        }
    });
    
    // Reset button
    resetBtn.addEventListener('click', function() {
        brightnessSlider.value = 100;
        contrastSlider.value = 100;
        saturationSlider.value = 100;
        updateFilters();
    });
    
    // Cleanup on page unload
    window.addEventListener('beforeunload', function() {
        if (filePaths.length > 0) {
            // Use sendBeacon for reliable delivery during page unload
            const payload = JSON.stringify({
                files: filePaths,
                session_id: sessionId
            });
            
            // Attempt to clean up files
            navigator.sendBeacon('/api/cleanup', payload);
        }
    });
    
    // More robust cleanup - also try on page visibility change
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'hidden' && filePaths.length > 0) {
            // Use fetch with keepalive flag as backup for sendBeacon
            fetch('/api/cleanup', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    files: filePaths,
                    session_id: sessionId
                }),
                keepalive: true
            }).catch(e => console.log('Cleanup attempt on visibility change failed:', e));
        }
    });
    
    // Smooth scroll for navigation and other UI functionality remains unchanged
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const targetId = this.getAttribute('href');
            const targetElement = document.querySelector(targetId);
            
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Animation for page elements on scroll
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.feature-card');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const windowHeight = window.innerHeight;
            
            if (elementPosition < windowHeight - 100) {
                element.style.opacity = '1';
                element.style.transform = 'translateY(0)';
            }
        });
    };
    
    // Set initial state for animated elements
    document.querySelectorAll('.feature-card').forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease';
    });
    
    // Add scroll event listener
    window.addEventListener('scroll', animateOnScroll);
    
    // Trigger once on load
    setTimeout(animateOnScroll, 100);
});