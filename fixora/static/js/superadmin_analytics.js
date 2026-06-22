
    fetch("{% url 'get_analytics_data' %}")
        .then(response => response.json())
        .then(data => {
            // 1. Render Category Pie Chart
            new Chart(document.getElementById('categoryChart'), {
                type: 'pie',
                data: {
                    labels: data.categories.map(c => c.category),
                    datasets: [{ data: data.categories.map(c => c.count), backgroundColor: ['#2563eb', '#10b981', '#f59e0b'] }]
                }
            });

            // 2. Render Activity Trend Line Chart
            new Chart(document.getElementById('trendChart'), {
                type: 'line',
                data: {
                    labels: data.daily.map(d => d.created_at__date),
                    datasets: [{ 
                        label: 'Complaints',
                        data: data.daily.map(d => d.count),
                        borderColor: '#2563eb',
                        tension: 0.3
                    }]
                }
            });
        });
