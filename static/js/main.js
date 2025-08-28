/**
 * PDF Tools Pro - Main JavaScript File
 * Common functionality for file handling and UI interactions
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize all components
    initializeTooltips();
    initializeNavigation();
    initializeGlobalFileHandling();
});

/**
 * Initialize Bootstrap tooltips
 */
function initializeTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function(tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

/**
 * Initialize navigation highlighting
 */
function initializeNavigation() {
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link');
    
    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}

/**
 * Initialize global file handling for all pages
 */
function initializeGlobalFileHandling() {
    // Add global drag and drop prevention for the entire document
    document.addEventListener('dragover', function(e) {
        e.preventDefault();
    });
    
    document.addEventListener('drop', function(e) {
        // Only prevent default if not dropping on a designated drop zone
        if (!e.target.closest('.file-drop-zone')) {
            e.preventDefault();
        }
    });
}

/**
 * Setup file drop zone functionality
 * @param {HTMLElement} dropZone - The drop zone element
 * @param {HTMLInputElement} fileInput - The file input element
 * @param {boolean} multiple - Whether to accept multiple files
 */
function setupFileDropZone(dropZone, fileInput, multiple = false) {
    if (!dropZone || !fileInput) return;

    // Set multiple attribute if needed
    if (multiple) {
        fileInput.multiple = true;
    }

    // Drag events
    dropZone.addEventListener('dragenter', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragover', function(e) {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });

    dropZone.addEventListener('dragleave', function(e) {
        e.preventDefault();
        // Only remove dragover if leaving the drop zone entirely
        if (!dropZone.contains(e.relatedTarget)) {
            dropZone.classList.remove('dragover');
        }
    });

    dropZone.addEventListener('drop', function(e) {
        e.preventDefault();
        dropZone.classList.remove('dragover');

        const files = e.dataTransfer.files;
        if (files.length > 0) {
            // Validate file types
            const validFiles = Array.from(files).filter(file => {
                const accept = fileInput.accept;
                if (!accept) return true;
                
                const acceptedTypes = accept.split(',').map(type => type.trim());
                return acceptedTypes.some(type => {
                    if (type.startsWith('.')) {
                        return file.name.toLowerCase().endsWith(type.toLowerCase());
                    } else if (type.includes('*')) {
                        const mimeType = type.replace('*', '');
                        return file.type.startsWith(mimeType);
                    } else {
                        return file.type === type;
                    }
                });
            });

            if (validFiles.length === 0) {
                showGlobalAlert('Invalid file type. Please select the correct file format.', 'warning');
                return;
            }

            // Handle single vs multiple files
            if (multiple && fileInput.multiple) {
                // For multiple file inputs, add to existing files
                const dt = new DataTransfer();
                
                // Add existing files first
                if (fileInput.files) {
                    Array.from(fileInput.files).forEach(file => dt.items.add(file));
                }
                
                // Add new valid files
                validFiles.forEach(file => dt.items.add(file));
                fileInput.files = dt.files;
            } else {
                // For single file inputs, replace files
                const dt = new DataTransfer();
                validFiles.forEach(file => dt.items.add(file));
                fileInput.files = dt.files;
            }

            // Trigger change event
            fileInput.dispatchEvent(new Event('change', { bubbles: true }));
        }
    });

    // Click to browse
    dropZone.addEventListener('click', function(e) {
        // Prevent click on buttons and other interactive elements
        if (e.target.tagName !== 'BUTTON' && e.target.tagName !== 'INPUT' && !e.target.closest('button')) {
            fileInput.click();
        }
    });

    // File input change event
    fileInput.addEventListener('change', function() {
        updateDropZoneDisplay(dropZone, this.files);
    });
}

/**
 * Update drop zone display based on selected files
 * @param {HTMLElement} dropZone - The drop zone element
 * @param {FileList} files - The selected files
 */
function updateDropZoneDisplay(dropZone, files) {
    const textCenter = dropZone.querySelector('.text-center');
    if (!textCenter) return;

    if (files.length > 0) {
        const fileNames = Array.from(files).map(file => file.name).join(', ');
        const truncated = fileNames.length > 50 ? fileNames.substring(0, 50) + '...' : fileNames;
        
        textCenter.innerHTML = `
            <i class="fas fa-check-circle fa-2x text-success mb-2"></i>
            <p class="mb-1 text-success"><strong>${files.length} file(s) selected</strong></p>
            <p class="text-muted small">${truncated}</p>
            <p class="text-muted small">Click to change or drag new files</p>
        `;
    } else {
        // Reset to original state when no files
        const isMultiple = dropZone.querySelector('input[multiple]');
        const icon = isMultiple ? 'fa-cloud-upload-alt' : 'fa-cloud-upload-alt';
        const text = isMultiple ? 'Drag and drop your files here' : 'Drag and drop your file here';
        
        textCenter.innerHTML = `
            <i class="fas ${icon} fa-3x text-muted mb-3"></i>
            <p class="mb-2">${text}</p>
            <p class="text-muted">or</p>
        `;
    }
}

/**
 * Format file size in human readable format
 * @param {number} bytes - File size in bytes
 * @returns {string} Formatted file size
 */
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

/**
 * Show a global alert message
 * @param {string} message - The alert message
 * @param {string} type - The alert type (success, danger, warning, info)
 * @param {number} duration - Auto-hide duration in milliseconds (0 = no auto-hide)
 */
function showGlobalAlert(message, type = 'info', duration = 5000) {
    // Create alert container if it doesn't exist
    let alertContainer = document.getElementById('globalAlertContainer');
    if (!alertContainer) {
        alertContainer = document.createElement('div');
        alertContainer.id = 'globalAlertContainer';
        alertContainer.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 9999;
            max-width: 400px;
        `;
        document.body.appendChild(alertContainer);
    }

    // Create alert element
    const alertId = 'alert_' + Date.now();
    const alertElement = document.createElement('div');
    alertElement.id = alertId;
    alertElement.className = `alert alert-${type} alert-dismissible fade show mb-2`;
    alertElement.innerHTML = `
        <i class="fas fa-${getAlertIcon(type)} me-2"></i>
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;

    // Add to container
    alertContainer.appendChild(alertElement);

    // Auto-hide if duration is specified
    if (duration > 0) {
        setTimeout(() => {
            const alert = document.getElementById(alertId);
            if (alert) {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }
        }, duration);
    }
}

/**
 * Get appropriate icon for alert type
 * @param {string} type - Alert type
 * @returns {string} Font Awesome icon class
 */
function getAlertIcon(type) {
    const icons = {
        success: 'check-circle',
        danger: 'exclamation-triangle',
        warning: 'exclamation-triangle',
        info: 'info-circle'
    };
    return icons[type] || 'info-circle';
}

/**
 * Validate file types against accepted types
 * @param {File} file - File to validate
 * @param {string} acceptedTypes - Accepted file types (e.g., '.pdf,.jpg')
 * @returns {boolean} Whether file is valid
 */
function validateFileType(file, acceptedTypes) {
    if (!acceptedTypes) return true;
    
    const types = acceptedTypes.split(',').map(type => type.trim().toLowerCase());
    const fileName = file.name.toLowerCase();
    const fileType = file.type.toLowerCase();
    
    return types.some(type => {
        if (type.startsWith('.')) {
            return fileName.endsWith(type);
        } else if (type.includes('/')) {
            return fileType === type;
        } else if (type.includes('*')) {
            const mimeCategory = type.replace('*', '');
            return fileType.startsWith(mimeCategory);
        }
        return false;
    });
}

/**
 * Create a loading spinner element
 * @param {string} text - Loading text
 * @returns {HTMLElement} Loading element
 */
function createLoadingElement(text = 'Processing...') {
    const loadingEl = document.createElement('div');
    loadingEl.className = 'text-center p-4';
    loadingEl.innerHTML = `
        <div class="spinner-border text-primary mb-3" role="status">
            <span class="visually-hidden">Loading...</span>
        </div>
        <p class="text-muted">${text}</p>
    `;
    return loadingEl;
}

/**
 * Animate progress bar
 * @param {HTMLElement} progressBar - Progress bar element
 * @param {number} targetPercent - Target percentage
 * @param {number} duration - Animation duration in ms
 */
function animateProgress(progressBar, targetPercent, duration = 1000) {
    const startPercent = parseInt(progressBar.style.width) || 0;
    const increment = (targetPercent - startPercent) / (duration / 16);
    let currentPercent = startPercent;

    const animate = () => {
        currentPercent += increment;
        if ((increment > 0 && currentPercent >= targetPercent) || 
            (increment < 0 && currentPercent <= targetPercent)) {
            progressBar.style.width = targetPercent + '%';
        } else {
            progressBar.style.width = currentPercent + '%';
            requestAnimationFrame(animate);
        }
    };

    animate();
}

/**
 * Debounce function to limit function calls
 * @param {Function} func - Function to debounce
 * @param {number} wait - Wait time in ms
 * @returns {Function} Debounced function
 */
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

/**
 * Copy text to clipboard
 * @param {string} text - Text to copy
 * @returns {Promise} Promise that resolves when text is copied
 */
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showGlobalAlert('Copied to clipboard!', 'success', 2000);
    } catch (err) {
        // Fallback for older browsers
        const textArea = document.createElement('textarea');
        textArea.value = text;
        document.body.appendChild(textArea);
        textArea.select();
        document.execCommand('copy');
        document.body.removeChild(textArea);
        showGlobalAlert('Copied to clipboard!', 'success', 2000);
    }
}

/**
 * Download file as blob
 * @param {Blob} blob - File blob
 * @param {string} filename - Filename for download
 */
function downloadBlob(blob, filename) {
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    window.URL.revokeObjectURL(url);
}

// Export functions for use in other files
window.PDFTools = {
    setupFileDropZone,
    formatFileSize,
    showGlobalAlert,
    validateFileType,
    createLoadingElement,
    animateProgress,
    debounce,
    copyToClipboard,
    downloadBlob
};
