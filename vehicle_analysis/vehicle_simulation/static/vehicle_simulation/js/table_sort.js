document.addEventListener('DOMContentLoaded', function () {
    const sortableHeaders = document.querySelectorAll('.sortable');

    sortableHeaders.forEach(header => {
        header.addEventListener('click', function () {
            const sortBy = this.getAttribute('data-sort');
            const table = document.getElementById('resultsTable');
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isAsc = this.classList.contains('asc');

            // Reset all headers
            sortableHeaders.forEach(h => {
                h.classList.remove('asc', 'desc');
                const arrow = h.querySelector('.sort-arrow');
                arrow.innerHTML = '↕';
            });

            // Sort rows
            rows.sort((a, b) => {
                const aValue = parseFloat(a.getAttribute(`data-${sortBy}`));
                const bValue = parseFloat(b.getAttribute(`data-${sortBy}`));

                return isAsc ? aValue - bValue : bValue - aValue;
            });

            // Update arrow and class
            const arrow = this.querySelector('.sort-arrow');
            if (isAsc) {
                this.classList.add('desc');
                arrow.innerHTML = '↓';
            } else {
                this.classList.add('asc');
                arrow.innerHTML = '↑';
            }

            // Rebuild table
            rows.forEach(row => tbody.appendChild(row));
        });
    });
});