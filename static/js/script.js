// Custom JavaScript

// Update current time in the navbar
function updateCurrentTime() {
    const timeElement = document.getElementById('current-time');
    if (timeElement) {
        const now = new Date();
        timeElement.textContent = now.toLocaleTimeString();
    }
}

// Update classroom status
function updateClassroomStatus() {
    const statusElements = document.querySelectorAll('[data-classroom-id]');
    statusElements.forEach(element => {
        const classroomId = element.dataset.classroomId;
        fetch(`/classrooms/${classroomId}/status`)
            .then(response => response.json())
            .then(data => {
                if (data.occupied) {
                    element.innerHTML = `
                        <div class="classroom-status occupied">
                            <h6>Currently Occupied</h6>
                            <p class="mb-0">
                                <strong>Subject:</strong> ${data.subject}<br>
                                <strong>Faculty:</strong> ${data.faculty}<br>
                                <strong>Time Remaining:</strong> ${data.time_remaining}
                            </p>
                        </div>
                    `;
                } else if (data.next_class) {
                    element.innerHTML = `
                        <div class="classroom-status available">
                            <h6>Available</h6>
                            <p class="mb-0">
                                <strong>Next Class:</strong> ${data.next_class.subject}<br>
                                <strong>Time:</strong> ${data.next_class.time}
                            </p>
                        </div>
                    `;
                } else {
                    element.innerHTML = `
                        <div class="classroom-status available">
                            <h6>Available</h6>
                            <p class="mb-0">No upcoming classes scheduled.</p>
                        </div>
                    `;
                }
            })
            .catch(error => {
                console.error('Error fetching classroom status:', error);
                element.innerHTML = `
                    <div class="alert alert-danger">
                        Error loading status. Please try again later.
                    </div>
                `;
            });
    });
}

// Filter classrooms
function filterClassrooms() {
    const department = document.getElementById('department').value.toLowerCase();
    const roomType = document.getElementById('room_type').value;
    const capacity = document.getElementById('capacity').value;
    
    const classrooms = document.querySelectorAll('.classroom-card');
    classrooms.forEach(card => {
        const cardDepartment = card.dataset.department.toLowerCase();
        const cardRoomType = card.dataset.roomType;
        const cardCapacity = parseInt(card.dataset.capacity);
        
        const departmentMatch = !department || cardDepartment.includes(department);
        const roomTypeMatch = !roomType || cardRoomType === roomType;
        const capacityMatch = !capacity || cardCapacity >= parseInt(capacity);
        
        if (departmentMatch && roomTypeMatch && capacityMatch) {
            card.style.display = '';
        } else {
            card.style.display = 'none';
        }
    });
}

// Initialize tooltips
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
}

// Initialize popovers
function initPopovers() {
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
}

// File input validation
function validateFileInput(input) {
    const allowedTypes = ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'image/jpeg', 'image/png'];
    const maxSize = 5 * 1024 * 1024; // 5MB
    
    const file = input.files[0];
    if (file) {
        if (!allowedTypes.includes(file.type)) {
            alert('Invalid file type. Please upload a PDF, DOC, DOCX, JPG, or PNG file.');
            input.value = '';
            return false;
        }
        
        if (file.size > maxSize) {
            alert('File size exceeds 5MB limit.');
            input.value = '';
            return false;
        }
    }
    return true;
}

// Initialize all functions when the DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Update time every second
    updateCurrentTime();
    setInterval(updateCurrentTime, 1000);
    
    // Update classroom status every 5 minutes
    updateClassroomStatus();
    setInterval(updateClassroomStatus, 300000);
    
    // Initialize Bootstrap components
    initTooltips();
    initPopovers();
    
    // Add event listeners for filters
    const filterInputs = document.querySelectorAll('[data-filter]');
    filterInputs.forEach(input => {
        input.addEventListener('change', filterClassrooms);
        input.addEventListener('keyup', filterClassrooms);
    });
    
    // Add event listeners for file inputs
    const fileInputs = document.querySelectorAll('input[type="file"]');
    fileInputs.forEach(input => {
        input.addEventListener('change', function() {
            validateFileInput(this);
        });
    });
}); 