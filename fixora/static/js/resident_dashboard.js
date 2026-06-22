// Asynchronous submit handler execution using AJAX/Fetch API
document.getElementById('complaintForm').addEventListener('submit', function (e) {
    e.preventDefault();

    const form = this;
    const submitBtn = form.querySelector('button[type="submit"]');
    const originalBtnText = submitBtn.innerHTML;

    // UI Loading State to prevent double submissions
    submitBtn.disabled = true;
    submitBtn.innerHTML = `
            <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
            Submitting...
        `;

    const formData = new FormData(form);
    
    // FIX 1: Get the exact URL from the form's "action" attribute
    const targetUrl = form.getAttribute('action'); 
    
    // FIX 2: Grab the generated CSRF token from the hidden input Django creates inside the form
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value; 

    fetch(targetUrl, {
        method: "POST",
        body: formData,
        headers: {
            "X-CSRFToken": csrfToken
        }
    })
        .then(response => {
            // FIX 3: Check if it's OK, OR if Django successfully redirected us back to the dashboard
            if (response.ok || response.redirected) {
                // Instantly refresh window view to render new database state cleanly
                window.location.reload();
            } else {
                alert("Something went wrong. Please check your form data and try again.");
                submitBtn.disabled = false;
                submitBtn.innerHTML = originalBtnText;
            }
        })
        .catch(error => {
            console.error("Submission Error:", error);
            alert("Network error. Could not connect to backend service.");
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalBtnText;
        });
});

// Helper linking dashboard Quick Actions tiles directly to modal variables
function openQuickComplaint(categoryName) {
    document.getElementById('modalTitle').value = categoryName + " maintenance required";
    document.querySelector('input[name="category"]').value = categoryName.toLowerCase();
    document.querySelector('.form-control.d-flex.align-items-center.fw-semibold').innerText = categoryName;

    var myModal = new bootstrap.Modal(document.getElementById('complaintModal'));
    myModal.show();
}