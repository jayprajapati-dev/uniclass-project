document.addEventListener('DOMContentLoaded', function() {
    // Image Preview for Listing Creation
    const imageInput = document.querySelector('input[type="file"]');
    if (imageInput) {
        imageInput.addEventListener('change', function(e) {
            const previewContainer = document.querySelector('.image-preview');
            if (!previewContainer) return;
            
            previewContainer.innerHTML = '';
            
            for (let i = 0; i < e.target.files.length; i++) {
                const file = e.target.files[i];
                if (file.type.startsWith('image/')) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        const img = document.createElement('img');
                        img.src = e.target.result;
                        img.classList.add('preview-image');
                        previewContainer.appendChild(img);
                    }
                    reader.readAsDataURL(file);
                }
            }
        });
    }
    
    // Price Range Slider
    const minPriceInput = document.querySelector('input[name="min_price"]');
    const maxPriceInput = document.querySelector('input[name="max_price"]');
    if (minPriceInput && maxPriceInput) {
        minPriceInput.addEventListener('change', function() {
            if (parseFloat(this.value) > parseFloat(maxPriceInput.value)) {
                maxPriceInput.value = this.value;
            }
        });
        
        maxPriceInput.addEventListener('change', function() {
            if (parseFloat(this.value) < parseFloat(minPriceInput.value)) {
                minPriceInput.value = this.value;
            }
        });
    }
    
    // Search Form Auto-Submit
    const searchForm = document.querySelector('.search-form');
    if (searchForm) {
        const inputs = searchForm.querySelectorAll('select, input');
        inputs.forEach(input => {
            input.addEventListener('change', function() {
                searchForm.submit();
            });
        });
    }
    
    // Listing Status Badge Colors
    const statusBadges = document.querySelectorAll('.listing-status');
    statusBadges.forEach(badge => {
        const status = badge.textContent.trim().toLowerCase();
        switch (status) {
            case 'available':
                badge.style.backgroundColor = '#28a745';
                break;
            case 'reserved':
                badge.style.backgroundColor = '#ffc107';
                break;
            case 'sold':
                badge.style.backgroundColor = '#dc3545';
                break;
        }
    });
    
    // Smooth Scrolling for Pagination
    const paginationLinks = document.querySelectorAll('.pagination a');
    paginationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector('.marketplace-content');
            if (target) {
                target.scrollIntoView({ behavior: 'smooth' });
                setTimeout(() => {
                    window.location.href = this.href;
                }, 500);
            }
        });
    });
    
    // Image Gallery for Listing Details
    const listingImages = document.querySelectorAll('.listing-gallery img');
    if (listingImages.length > 0) {
        const mainImage = document.querySelector('.main-image');
        if (mainImage) {
            listingImages.forEach(img => {
                img.addEventListener('click', function() {
                    mainImage.src = this.src;
                    mainImage.alt = this.alt;
                });
            });
        }
    }
    
    // Message Form Auto-Resize
    const messageForm = document.querySelector('.message-form textarea');
    if (messageForm) {
        messageForm.addEventListener('input', function() {
            this.style.height = 'auto';
            this.style.height = (this.scrollHeight) + 'px';
        });
    }
    
    // Real-time Updates for Messages
    const messageContainer = document.querySelector('.message-container');
    if (messageContainer) {
        // Scroll to bottom of messages
        messageContainer.scrollTop = messageContainer.scrollHeight;
        
        // Check for new messages periodically
        setInterval(() => {
            const lastMessageId = document.querySelector('.message:last-child')?.dataset.messageId;
            if (lastMessageId) {
                fetch(`/marketplace/messages/check-new?last_id=${lastMessageId}`)
                    .then(response => response.json())
                    .then(data => {
                        if (data.new_messages) {
                            location.reload();
                        }
                    });
            }
        }, 5000);
    }
    
    // Rating Stars Interaction
    const ratingInputs = document.querySelectorAll('.rating-input');
    ratingInputs.forEach(input => {
        const stars = input.querySelectorAll('.star');
        stars.forEach(star => {
            star.addEventListener('mouseover', function() {
                const value = this.dataset.value;
                stars.forEach(s => {
                    if (s.dataset.value <= value) {
                        s.classList.add('hover');
                    } else {
                        s.classList.remove('hover');
                    }
                });
            });
            
            star.addEventListener('mouseout', function() {
                stars.forEach(s => s.classList.remove('hover'));
            });
            
            star.addEventListener('click', function() {
                const value = this.dataset.value;
                input.querySelector('input[type="hidden"]').value = value;
                stars.forEach(s => {
                    if (s.dataset.value <= value) {
                        s.classList.add('selected');
                    } else {
                        s.classList.remove('selected');
                    }
                });
            });
        });
    });
    
    // Dynamic subject loading
    const departmentSelect = document.querySelector('select[name="department"]');
    const semesterSelect = document.querySelector('select[name="semester"]');
    const subjectSelect = document.querySelector('select[name="subject"]');
    
    function updateSubjects() {
        const department = departmentSelect.value;
        const semester = semesterSelect.value;
        
        if (department === 'all' || semester === 'all') {
            subjectSelect.innerHTML = '<option value="all">All Subjects</option>';
            return;
        }
        
        fetch(`/marketplace/get-subjects?department=${department}&semester=${semester}`)
            .then(response => response.json())
            .then(data => {
                let options = '<option value="all">All Subjects</option>';
                data.subjects.forEach(subject => {
                    options += `<option value="${subject.id}">${subject.name}</option>`;
                });
                subjectSelect.innerHTML = options;
            });
    }
    
    if (departmentSelect && semesterSelect && subjectSelect) {
        departmentSelect.addEventListener('change', updateSubjects);
        semesterSelect.addEventListener('change', updateSubjects);
    }
}); 