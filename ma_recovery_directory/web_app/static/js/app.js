// JavaScript for Massachusetts Recovery Services Directory

document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const clearBtn = document.getElementById('clearBtn');
    const exportBtn = document.getElementById('exportBtn');
    const resultsContainer = document.getElementById('results');
    const noResultsDiv = document.getElementById('noResults');
    const resultCount = document.getElementById('resultCount');
    
    let currentResults = [];

    // Load initial statistics
    loadStatistics();

    // Search form submission
    searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        performSearch();
    });

    // Clear button
    clearBtn.addEventListener('click', function() {
        searchForm.reset();
        clearResults();
    });

    // Export button
    exportBtn.addEventListener('click', function() {
        exportResults();
    });

    function performSearch() {
        const filters = {
            zip_code: document.getElementById('zipCode').value,
            service_type: document.getElementById('serviceType').value,
            language: document.getElementById('language').value,
            population: document.getElementById('population').value
        };

        fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filters)
        })
        .then(response => response.json())
        .then(data => {
            currentResults = data;
            displayResults(data);
        })
        .catch(error => {
            console.error('Error:', error);
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
            
            results.forEach(service => {
                const serviceCard = createServiceCard(service);
                resultsContainer.appendChild(serviceCard);
            });
        }
    }

    function createServiceCard(service) {
        const col = document.createElement('div');
        col.className = 'col-md-6 col-lg-4';
        
        const card = document.createElement('div');
        card.className = 'card service-card';
        
        const serviceTypes = service.service_types ? service.service_types.split(',').map(s => s.trim()) : [];
        const languages = service.languages ? service.languages.split(',').map(l => l.trim()) : [];
        const populations = service.populations_served ? service.populations_served.split(',').map(p => p.trim()) : [];
        
        card.innerHTML = `
            <div class="service-header">
                <h6 class="mb-0">${service.name || 'N/A'}</h6>
            </div>
            <div class="service-body">
                <div class="service-info">
                    <strong>Address:</strong><br>
                    ${service.address || 'N/A'}<br>
                    ${service.city || ''}, ${service.state || ''} ${service.zip_code || ''}
                </div>
                
                ${service.hours ? `<div class="service-info"><strong>Hours:</strong> ${service.hours}</div>` : ''}
                
                ${serviceTypes.length > 0 ? `
                <div class="service-info">
                    <strong>Services:</strong><br>
                    ${serviceTypes.map(type => `<span class="badge badge-service">${type}</span>`).join('')}
                </div>` : ''}
                
                ${languages.length > 0 ? `
                <div class="service-info">
                    <strong>Languages:</strong><br>
                    ${languages.map(lang => `<span class="badge badge-language">${lang}</span>`).join('')}
                </div>` : ''}
                
                ${populations.length > 0 ? `
                <div class="service-info">
                    <strong>Populations Served:</strong><br>
                    ${populations.map(pop => `<span class="badge badge-population">${pop}</span>`).join('')}
                </div>` : ''}
                
                ${service.eligibility ? `<div class="service-info"><strong>Eligibility:</strong> ${service.eligibility}</div>` : ''}
                
                <div class="contact-info">
                    ${service.phone ? `<div><strong>Phone:</strong> <a href="tel:${service.phone}">${service.phone}</a></div>` : ''}
                    ${service.email ? `<div><strong>Email:</strong> <a href="mailto:${service.email}">${service.email}</a></div>` : ''}
                    ${service.website ? `<div><strong>Website:</strong> <a href="${service.website}" target="_blank">Visit Site</a></div>` : ''}
                </div>
            </div>
        `;
        
        col.appendChild(card);
        return col;
    }

    function clearResults() {
        resultsContainer.innerHTML = '';
        noResultsDiv.style.display = 'none';
        exportBtn.disabled = true;
        resultCount.textContent = '0 results';
        currentResults = [];
    }

    function exportResults() {
        if (currentResults.length === 0) {
            showError('No results to export.');
            return;
        }

        const filters = {
            zip_code: document.getElementById('zipCode').value,
            service_type: document.getElementById('serviceType').value,
            language: document.getElementById('language').value,
            population: document.getElementById('population').value
        };

        fetch('/api/export', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filters)
        })
        .then(response => {
            if (response.ok) {
                return response.blob();
            }
            throw new Error('Export failed');
        })
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.style.display = 'none';
            a.href = url;
            a.download = 'recovery_services.csv';
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        })
        .catch(error => {
            console.error('Error:', error);
            showError('An error occurred while exporting. Please try again.');
        });
    }

    function loadStatistics() {
        fetch('/api/stats')
        .then(response => response.json())
        .then(data => {
            document.getElementById('totalServices').textContent = data.total_services || 0;
            document.getElementById('citiesCovered').textContent = data.cities_covered || 0;
            document.getElementById('serviceTypes').textContent = data.service_types || 0;
        })
        .catch(error => {
            console.error('Error loading statistics:', error);
        });
    }

    function showError(message) {
        // Create a simple alert for errors
        const alert = document.createElement('div');
        alert.className = 'alert alert-danger alert-dismissible fade show';
        alert.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const container = document.querySelector('.container');
        container.insertBefore(alert, container.firstChild);
        
        // Auto-dismiss after 5 seconds
        setTimeout(() => {
            alert.remove();
        }, 5000);
    }
});