// 1. Toggle the sidebar when the hamburger menu is clicked
        function toggleSidebar() {
            document.querySelector('.sidebar').classList.toggle('show');
        }

        // 2. Close the sidebar when clicking anywhere outside of it
        document.addEventListener('click', function(event) {
            const sidebar = document.querySelector('.sidebar');
            const toggleButton = document.querySelector('.sidebar-toggle');
            
            // Check if the click happened on mobile (where sidebar has the 'show' class)
            if (sidebar.classList.contains('show')) {
                // If the click was NOT inside the sidebar, and NOT on the toggle button itself
                if (!sidebar.contains(event.target) && !toggleButton.contains(event.target)) {
                    sidebar.classList.remove('show'); // Hide it
                }
            }
        });