document.addEventListener('DOMContentLoaded', function () {
    const searchForm = document.getElementById('searchForm');
    const clearBtn = document.getElementById('clearBtn');
    const exportBtn = document.getElementById('exportBtn');
    const resultsContainer = document.getElementById('results');
    const noResultsDiv = document.getElementById('noResults');
    const placeholder = document.getElementById('placeholder');
    const loadingSpinner = document.getElementById('loadingSpinner');
    const resultCount = document.getElementById('resultCount');

    let currentResults = [];

    loadStatistics();

    searchForm.addEventListener('submit', function (e) {
        e.preventDefault();
        performSearch();
    });

    clearBtn.addEventListener('click', function () {
        searchForm.reset();
        clearResults();
    });

    exportBtn.addEventListener('click', exportResults);

    function buildFilters() {
        return {
            text: document.getElementById('textSearch').value.trim(),
            zip_code: '',
            service_type: document.getElementById('serviceType').value,
            language: document.getElementById('language').value,
            population: document.getElementById('population').value,
            near_zip: document.getElementById('nearZip').value.trim(),
            max_miles: document.getElementById('maxMiles').value,
        };
    }

    function performSearch() {
        const filters = buildFilters();

        placeholder.style.display = 'none';
        loadingSpinner.style.display = 'block';
        resultsContainer.innerHTML = '';
        noResultsDiv.style.display = 'none';

        fetch('/api/search', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(filters),
        })
            .then(r => r.json())
            .then(data => {
                currentResults = data;
                loadingSpinner.style.display = 'none';
                displayResults(data);
            })
            .catch(() => {
                loadingSpinner.style.display = 'none';
                showError('An error occurred while searching. Please try again.');
            });
    }

    function displayResults(results) {
        resultsContainer.innerHTML = '';

        if (results.length === 0) {
            noResultsDiv.style.display = 'block';
            exportBtn.disabled = true;
            resultCount.textContent = '0 results';
        } else {
            noResultsDiv.style.display = 'none';
            exportBtn.disabled = false;
            resultCount.textContent = `${results.length} result${results.length !== 1 ? 's' : ''}`;
            results.forEach(service => resultsContainer.appendChild(createServiceCard(service)));
        }
    }

    function createServiceCard(service) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';

        const serviceTypes = splitField(service.service_types);
        const languages = splitField(service.languages);
        const populations = splitField(service.populations_served);

        const mapLink = (service.latitude && service.longitude)
            ? `<a href="/map#${service.id}" class="btn btn-sm btn-outline-secondary ms-1">
                 <i class="bi bi-map me-1"></i>Map
               </a>`
            : '';

        col.innerHTML = `
            <div class="card service-card h-100">
                <div class="service-header">
                    <span class="fw-semibold">${esc(service.name) || 'N/A'}</span>
                </div>
                <div class="service-body d-flex flex-column">
                    <div class="service-info">
                        <i class="bi bi-geo-alt text-muted me-1"></i>
                        ${esc(service.address) || 'N/A'}<br>
                        <span class="text-muted">${esc(service.city)}, ${esc(service.state)} ${esc(service.zip_code)}</span>
                    </div>

                    ${serviceTypes.length ? `
                    <div class="service-info">
                        ${serviceTypes.map(t => `<span class="badge badge-service">${esc(t)}</span>`).join('')}
                    </div>` : ''}

                    ${languages.length ? `
                    <div class="service-info">
                        ${languages.map(l => `<span class="badge badge-language">${esc(l)}</span>`).join('')}
                    </div>` : ''}

                    ${populations.length ? `
                    <div class="service-info">
                        ${populations.map(p => `<span class="badge badge-population">${esc(p)}</span>`).join('')}
                    </div>` : ''}

                    <div class="contact-info mt-auto">
                        ${service.phone ? `<div><i class="bi bi-telephone me-1"></i><a href="tel:${esc(service.phone)}">${esc(service.phone)}</a></div>` : ''}
                        ${service.email ? `<div><i class="bi bi-envelope me-1"></i><a href="mailto:${esc(service.email)}">${esc(service.email)}</a></div>` : ''}
                        ${service.website ? `<div><i class="bi bi-globe me-1"></i><a href="${esc(service.website)}" target="_blank" rel="noopener">Website</a></div>` : ''}
                    </div>
                    <div class="mt-2">
                        <a href="/provider/${service.id}" class="btn btn-sm btn-primary">
                            <i class="bi bi-info-circle me-1"></i>Details
                        </a>
                        ${mapLink}
                    </div>
                </div>
            </div>`;

        return col;
    }

    function clearResults() {
        resultsContainer.innerHTML = '';
        noResultsDiv.style.display = 'none';
        exportBtn.disabled = true;
        resultCount.textContent = '—';
        currentResults = [];
        placeholder.style.display = 'block';
    }

    function exportResults() {
        if (currentResults.length === 0) return;
        const filters = buildFilters();
        fetch('/api/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(filters),
        })
            .then(r => {
                if (!r.ok) throw new Error('Export failed');
                return r.blob();
            })
            .then(blob => {
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'recovery_services.csv';
                document.body.appendChild(a);
                a.click();
                URL.revokeObjectURL(url);
                a.remove();
            })
            .catch(() => showError('Export failed. Please try again.'));
    }

    function loadStatistics() {
        fetch('/api/stats')
            .then(r => r.json())
            .then(data => {
                document.getElementById('totalServices').textContent = data.total_services ?? '—';
                document.getElementById('citiesCovered').textContent = data.cities_covered ?? '—';
                const sources = data.data_sources ? Object.keys(data.data_sources).length : '—';
                document.getElementById('dataSources').textContent = sources;
            })
            .catch(() => {});
    }

    function showError(message) {
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `${esc(message)}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
        document.querySelector('.container').prepend(alert);
        setTimeout(() => alert.remove(), 6000);
    }

    function splitField(value) {
        return value ? value.split(',').map(s => s.trim()).filter(Boolean) : [];
    }

    function esc(str) {
        if (str == null) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;');
    }
});
