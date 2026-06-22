// --- 1. PRIORITY SELECTION LOGIC ---
function setPriority(level, btnElement) {
    document.getElementById('priorityValue').value = level;
    const buttons = btnElement.parentElement.querySelectorAll('.priority-btn');
    buttons.forEach(btn => btn.classList.remove('active'));
    btnElement.classList.add('active');
}

// --- 2. ADVANCED DRAG AND DROP IMAGE UPLOAD ---
const dropZone = document.getElementById('dropZone');
const fileInput = document.getElementById('fileInput');
const fileFeedback = document.getElementById('fileFeedback');

// Prevent default browser behaviors for drag/drop (which usually open the file)
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false);
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Add visual highlight when dragging a file over the zone
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.style.borderColor = '#2563eb';
        dropZone.style.backgroundColor = '#eff6ff';
        dropZone.style.transform = 'scale(1.02)';
    }, false);
});

// Remove visual highlight when leaving the zone or dropping
['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => {
        dropZone.style.borderColor = '#cbd5e1';
        dropZone.style.backgroundColor = '#f8fafc';
        dropZone.style.transform = 'scale(1)';
    }, false);
});

// Handle the actual drop event
dropZone.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;

    // Assign the dropped files to the hidden input
    fileInput.files = files;

    // Trigger the visual feedback function
    handleFileSelect(fileInput);
}, false);

function handleFileSelect(inputElement) {
        const fileFeedback = document.getElementById('fileFeedback');
        
        if (inputElement.files && inputElement.files.length > 0) {
            const uploadedFile = inputElement.files[0];
            const fileName = uploadedFile.name;
            const fileSize = (uploadedFile.size / (1024 * 1024)).toFixed(2); // Convert to MB
            
            // 1. STRICT FILE TYPE VALIDATION
            if (!uploadedFile.type.startsWith('image/')) {
                fileFeedback.innerHTML = `
                    <span class="text-danger fw-bold d-inline-flex align-items-center gap-1 mt-1">
                        <i class="bi bi-x-circle-fill"></i> Invalid file. Images only (JPG, PNG).
                    </span>`;
                inputElement.value = ''; // Reject and clear the input
                return;
            }

            // 2. VALIDATE FILE SIZE (5MB)
            if (fileSize > 5) {
                fileFeedback.innerHTML = `
                    <span class="text-danger fw-bold d-inline-flex align-items-center gap-1 mt-1">
                        <i class="bi bi-x-circle-fill"></i> File too large (${fileSize} MB). Max 5 MB.
                    </span>`;
                inputElement.value = ''; // Reject and clear the input
                return;
            }

            // Success State
            fileFeedback.innerHTML = `
                <span class="text-success fw-bold d-inline-flex align-items-center gap-1 mt-1">
                    <i class="bi bi-check-circle-fill"></i> Loaded: ${fileName}
                </span>
            `;
        } else {
            // Reset to default if cleared
            fileFeedback.innerHTML = "Max 1 image, 5 MB each";
            fileFeedback.className = "text-muted mt-2 mb-0";
        }
    }