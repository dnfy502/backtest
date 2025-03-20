document.addEventListener('DOMContentLoaded', function() {
    const dropArea = document.getElementById('drop-area');
    const fileInput = document.getElementById('fileInput');
    const fileName = document.getElementById('file-name');
    const generateBtn = document.getElementById('generate-btn');
    const loading = document.getElementById('loading');
    const results = document.getElementById('results');
    const reportData = document.getElementById('report-data');
    const chartDiv = document.getElementById('chart');
    
    let selectedFile = null;
    
    // Prevent default drag behaviors
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, preventDefaults, false);
    });
    
    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
    
    // Highlight drop area when file is dragged over it
    ['dragenter', 'dragover'].forEach(eventName => {
        dropArea.addEventListener(eventName, highlight, false);
    });
    
    ['dragleave', 'drop'].forEach(eventName => {
        dropArea.addEventListener(eventName, unhighlight, false);
    });
    
    function highlight() {
        dropArea.classList.add('highlight');
    }
    
    function unhighlight() {
        dropArea.classList.remove('highlight');
    }
    
    // Handle dropped files
    dropArea.addEventListener('drop', handleDrop, false);
    
    function handleDrop(e) {
        const dt = e.dataTransfer;
        const file = dt.files[0];
        handleFile(file);
    }
    
    // Handle file input change
    fileInput.addEventListener('change', function() {
        if (fileInput.files.length > 0) {
            handleFile(fileInput.files[0]);
        }
    });
    
    // Click on drop area triggers file input
    dropArea.addEventListener('click', function() {
        fileInput.click();
    });
    
    function handleFile(file) {
        if (file && file.type === 'text/csv') {
            selectedFile = file;
            fileName.textContent = file.name;
            generateBtn.disabled = false;
        } else {
            alert('Please upload a CSV file');
            selectedFile = null;
            fileName.textContent = '';
            generateBtn.disabled = true;
        }
    }
    
    // Generate report button click handler
    generateBtn.addEventListener('click', function() {
        if (!selectedFile) return;
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        
        // Show loading spinner
        loading.classList.remove('hidden');
        results.classList.add('hidden');
        generateBtn.disabled = true;
        
        fetch('/upload', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                alert(data.error);
                return;
            }
            
            // Hide loading spinner
            loading.classList.add('hidden');
            
            // Display results
            displayResults(data.results);
            displayChart(data.chart);
            results.classList.remove('hidden');
        })
        .catch(error => {
            console.error('Error:', error);
            alert('An error occurred while processing your file');
            loading.classList.add('hidden');
            generateBtn.disabled = false;
        });
    });
    
    function displayResults(results) {
        reportData.innerHTML = '';
        
        const metrics = [
            { key: 'Initial_Balance', label: 'Initial Balance', format: '$' },
            { key: 'Final_Balance', label: 'Final Balance', format: '$' },
            { key: 'Benchmark_Portfolio', label: 'Benchmark Portfolio', format: '$' },
            { key: 'Net_Profit', label: 'Net Profit', format: '%' },
            { key: 'Benchmark_Return', label: 'Benchmark Return', format: '%' },
            { key: 'No_of_Trades', label: 'Number of Trades', format: '' },
            { key: 'Average_Return', label: 'Avg Return per Trade', format: '$' },
            { key: 'Winning_Trades', label: 'Winning Trades', format: '' },
            { key: 'Losing_Trades', label: 'Losing Trades', format: '' },
            { key: 'Win_Rate', label: 'Win Rate', format: '%' },
            { key: 'Max_Balance', label: 'Max Balance', format: '$' },
            { key: 'Min_Balance', label: 'Min Balance', format: '$' },
            { key: 'Max_Win', label: 'Max Win', format: '$' },
            { key: 'Max_Loss', label: 'Max Loss', format: '$' },
            { key: 'Average_Win', label: 'Average Win', format: '$' },
            { key: 'Average_Loss', label: 'Average Loss', format: '$' },
            { key: 'Total_Fees', label: 'Total Fees', format: '$' },
            { key: 'Long_Trades', label: 'Long Trades', format: '' },
            { key: 'Short_Trades', label: 'Short Trades', format: '' }
        ];
        
        metrics.forEach(metric => {
            const metricDiv = document.createElement('div');
            metricDiv.className = 'metric';
            
            const title = document.createElement('h3');
            title.textContent = metric.label;
            
            const value = document.createElement('p');
            value.textContent = results[metric.key] + metric.format;
            
            metricDiv.appendChild(title);
            metricDiv.appendChild(value);
            reportData.appendChild(metricDiv);
        });
    }
    
    function displayChart(chartJson) {
        const chart = JSON.parse(chartJson);
        Plotly.newPlot(chartDiv, chart.data, chart.layout);
    }
});