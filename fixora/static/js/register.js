function toggleFields() {
        const role = document.getElementById('roleSelect').value;
        const residentField = document.getElementById('residentField');
        const workerField = document.getElementById('workerField');
        const flatInput = document.getElementById('flatInput');
        const workerInput = document.getElementById('workerInput');

        if (role === 'resident') {
            residentField.style.display = 'block';
            workerField.style.display = 'none';
            flatInput.required = true;
            workerInput.required = false;
        } else if (role === 'worker') {
            residentField.style.display = 'none';
            workerField.style.display = 'block';
            flatInput.required = false;
            workerInput.required = true;
        }
    }