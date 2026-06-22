
    // Dictionary tracking UI colors/icons across selections
    const categoryMetadata = {
        plumbing: { icon: "bi-droplet", style: "background: #eff6ff; color: #2563eb;" },
        electrical: { icon: "bi-lightning-charge", style: "background: #fef9c3; color: #ca8a04;" },
        cleaning: { icon: "bi-brush", style: "background: #dcfce7; color: #16a34a;" },
        glass: { icon: "bi-square", style: "background: #e0f2fe; color: #0284c7;" },
        tiles: { icon: "bi-grid-3x3-gap", style: "background: #e0e7ff; color: #4f46e5;" },
        other: { icon: "bi-three-dots", style: "background: #ffedd5; color: #ea580c;" }
    };

    // Set minimum date to today on load
    document.addEventListener("DOMContentLoaded", function() {
        const dateInput = document.getElementById('dateInput');
        const today = new Date().toISOString().split('T')[0];
        dateInput.setAttribute('min', today);
    });

    function setServiceCategory(catName, tileElement) {
        document.getElementById('categoryValue').value = catName;
        document.querySelectorAll('.category-tile').forEach(tile => tile.classList.remove('active'));
        tileElement.classList.add('active');
        
        // Update live sidebar text & match colors accurately
        document.getElementById('summaryCategoryText').innerText = catName;
        const meta = categoryMetadata[catName];
        const iconContainer = document.getElementById('summaryCategoryIcon');
        iconContainer.innerHTML = `<i class="bi ${meta.icon}"></i>`;
        iconContainer.setAttribute('style', meta.style);
    }

    function updateSummary() {
        const dateVal = document.getElementById('dateInput').value;
        const timeVal = document.getElementById('timeInput').value;

        // Update card parameters
        if(dateVal) {
            const parsedDate = new Date(dateVal);
            document.getElementById('summaryDateText').innerText = parsedDate.toLocaleDateString('en-US', { day: 'numeric', month: 'short', year: 'numeric' });
        }
        if(timeVal) document.getElementById('summaryTimeText').innerText = timeVal;

        // Form confirmation completion checks to unlock CTA button state
        const confirmBtn = document.getElementById('confirmButton');
        if (dateVal && timeVal) {
            confirmBtn.disabled = false;
            confirmBtn.style.backgroundColor = "#1d4ed8";
            confirmBtn.style.color = "#ffffff";
        } else {
            confirmBtn.disabled = true;
            confirmBtn.style.backgroundColor = "#e2e8f0";
            confirmBtn.style.color = "#94a3b8";
        }
    }

    // --- ADVANCED DRAG AND DROP IMAGE UPLOAD ---
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const fileFeedback = document.getElementById('fileFeedback');

    // Prevent default browser behaviors for drag/drop (which usually open the file in a new tab)
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults (e) {
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
        const feedback = document.getElementById('fileFeedback');
        
        if(inputElement.files && inputElement.files.length > 0) {
            const file = inputElement.files[0];
            const fileSize = (file.size / (1024 * 1024)).toFixed(2);
            
            // 1. STRICT FILE TYPE VALIDATION (Blocks PDFs, Docs, etc.)
            if (!file.type.startsWith('image/')) {
                feedback.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-x-circle-fill"></i> Invalid file. Please upload an image (JPG, PNG).</span>`;
                inputElement.value = ''; // Immediately clear the input
                document.getElementById('summaryPhotosText').innerText = `0 photo(s) added`;
                return; // Stop execution
            }

            // 2. FILE SIZE VALIDATION
            if (fileSize > 5) {
                feedback.innerHTML = `<span class="text-danger fw-bold"><i class="bi bi-x-circle-fill"></i> File too large (${fileSize} MB)</span>`;
                inputElement.value = ''; // clear
                document.getElementById('summaryPhotosText').innerText = `0 photo(s) added`;
            } else {
                // Success
                feedback.innerHTML = `<span class="text-success fw-bold"><i class="bi bi-check-circle-fill"></i> Loaded: ${file.name}</span>`;
                document.getElementById('summaryPhotosText').innerText = `1 photo added`;
            }
        } else {
            // Reset to default if cleared
            feedback.innerHTML = "Max 1 image, 5 MB each";
            feedback.className = "text-muted mt-2 mb-0";
            document.getElementById('summaryPhotosText').innerText = `0 photo(s) added`;
        }
    }
