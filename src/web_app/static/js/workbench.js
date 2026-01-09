document.addEventListener('DOMContentLoaded', function () {
    loadStagingData();

    // Upload Handler
    document.getElementById('uploadForm').addEventListener('submit', function (e) {
        e.preventDefault();

        const fileInput = document.getElementById('fileInput');
        const uploadBtn = document.getElementById('uploadBtn');
        // Tailwind spinner is an SVG with animate-spin class
        const spinner = uploadBtn.querySelector('svg.animate-spin');

        if (!fileInput.files[0]) {
            alert('Please select a file');
            return;
        }

        const formData = new FormData();
        formData.append('file', fileInput.files[0]);

        uploadBtn.disabled = true;
        if (spinner) spinner.classList.remove('hidden');

        fetch('/workbench/upload', {
            method: 'POST',
            body: formData
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert(data.message);
                    loadStagingData();
                    fileInput.value = ''; // Clear input
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('Upload failed');
            })
            .finally(() => {
                uploadBtn.disabled = false;
                if (spinner) spinner.classList.add('hidden');
            });
    });

    // Promote Handler
    document.getElementById('promoteBtn').addEventListener('click', function () {
        if (!confirm('Are you sure you want to promote all VALID records to production?')) return;

        fetch('/workbench/api/promote', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    alert(data.message);
                    loadStagingData();
                }
            })
            .catch(error => console.error('Error:', error));
    });

    // Clear Handler
    document.getElementById('clearBtn').addEventListener('click', function () {
        if (!confirm('Are you sure you want to clear ALL staging data? This cannot be undone.')) return;

        fetch('/workbench/api/clear', {
            method: 'POST'
        })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('Error: ' + data.error);
                } else {
                    loadStagingData();
                }
            })
            .catch(error => console.error('Error:', error));
    });
});

function loadStagingData() {
    // Add timestamp to prevent caching
    fetch('/workbench/api/staging-data?t=' + new Date().getTime())
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            console.log('Loaded data from API:', data); // Debug log

            if (!Array.isArray(data)) {
                console.error('Data is not an array:', data);
                return;
            }

            const tbody = document.getElementById('stagingTableBody');
            if (!tbody) {
                console.error('Table body element not found!');
                return;
            }

            console.log('Clearing table body...');
            tbody.innerHTML = '';

            let validCount = 0;
            let errorCount = 0;

            console.log(`Processing ${data.length} rows...`);

            if (data.length === 0) {
                console.log('No data found, showing empty message.');
                tbody.innerHTML = '<tr><td colspan="6" class="text-center py-4 text-gray-500">No data in staging</td></tr>';
            }

            data.forEach((row, index) => {
                console.log(`Rendering row ${index}:`, row);
                const tr = document.createElement('tr');

                // Status Badge
                let statusClass = 'bg-gray-100 text-gray-800';
                if (row.status === 'VALID') {
                    statusClass = 'bg-green-100 text-green-800';
                    validCount++;
                } else if (row.status === 'ERROR') {
                    statusClass = 'bg-red-100 text-red-800';
                    errorCount++;
                } else if (row.status === 'PROMOTED') {
                    statusClass = 'bg-blue-100 text-blue-800';
                }

                tr.innerHTML = `
                    <td class="px-6 py-4 whitespace-nowrap"><span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full ${statusClass}">${row.status}</span></td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.date || '-'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">${row.asset_id || '-'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${row.transaction_type || '-'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500 text-right">${row.amount ? row.amount.toFixed(2) : '-'}</td>
                    <td class="px-6 py-4 text-sm text-red-600">${row.validation_errors ? row.validation_errors.join(', ') : ''}</td>
                `;
                tbody.appendChild(tr);
            });

            document.getElementById('totalCount').textContent = `${data.length} Total`;
            document.getElementById('validCount').textContent = `${validCount} Valid`;
            document.getElementById('errorCount').textContent = `${errorCount} Errors`;
        })
        .catch(error => console.error('Error loading data:', error));
}
