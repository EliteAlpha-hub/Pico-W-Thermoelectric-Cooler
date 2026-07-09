def get_webpage():
    html = """<!DOCTYPE html>
<html>
<head>
    <title>Pico W Cooling Controller</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f5f5f5; }
        .container { max-width: 800px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        h1 { color: #333; text-align: center; }
        .panel { margin-bottom: 20px; padding: 15px; background: #f9f9f9; border-radius: 5px; }
        .panel h2 { margin-top: 0; color: #444; }
        .btn { display: inline-block; padding: 8px 15px; background: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 5px; border: none; cursor: pointer; }
        .btn:hover { background: #45a049; }
        .btn-off { background: #f44336; }
        .btn-off:hover { background: #d32f2f; }
        .btn-zip { background: #2196F3; }
        .btn-zip:hover { background: #0b7dda; }
        .btn-zap { background: #ff9800; }
        .btn-zap:hover { background: #e68a00; }
        .btn-zoom { background: #9c27b0; }
        .btn-zoom:hover { background: #7b1fa2; }
        .active { box-shadow: 0 0 0 2px #333; }
        .temp-display { font-size: 24px; font-weight: bold; text-align: center; margin: 15px 0; }
        .gauge { height: 20px; background: #e0e0e0; border-radius: 10px; margin: 10px 0; overflow: hidden; }
        .gauge-fill { height: 100%; background: #4CAF50; width: 0%; transition: width 0.5s; }
        .chart-container { height: 200px; margin: 20px 0; }
        .status { font-family: monospace; background: #333; color: #0f0; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        <h1>Pico W Cooling Controller</h1>
        
        <div class="panel">
            <h2>Current Status</h2>
            <div class="temp-display">
                <div>External: <span id="temp1">0.0</span>°C</div>
                <div>Internal: <span id="temp2">0.0</span>°C</div>
                <div>Difference: <span id="temp-diff">0.0</span>°C</div>
                <div>Target: <span id="target-temp">0.0</span>°C</div>
            </div>
            
            
            <div>Peltier Power: <span id="peltier-power">0</span>%</div>
            <div class="gauge"><div class="gauge-fill" id="peltier-gauge"></div></div>
            
            <div>Current Mode: <span id="current-mode">OFF</span></div>
        </div>
        
        <div class="panel">
            <h2>Cooling Modes</h2>
            <button id="btn-off" class="btn btn-off">OFF</button>
            <button id="btn-zip" class="btn btn-zip">ZIP (20°C)</button>
            <button id="btn-zap" class="btn btn-zap">ZAP (10°C)</button>
            <button id="btn-zoom" class="btn btn-zoom">ZOOM (MAX)</button>
        </div>
        
        <div class="panel">
            <h2>Temperature Chart</h2>
            <div class="chart-container">
                <canvas id="temp-chart"></canvas>
            </div>
        </div>
        
        <div class="panel">
            <h2>System Status</h2>
            <pre class="status" id="system-status">Loading...</pre>
        </div>
    </div>
    
    <script>
        // Global variables
        let tempChart;
        let tempData = { temp1: [], temp2: [], diff: [], labels: [] };
        const maxDataPoints = 30;
        
        // Initialize chart
        function initChart() {
            const ctx = document.getElementById('temp-chart').getContext('2d');
            tempChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: tempData.labels,
                    datasets: [
                        {
                            label: 'External Temp (°C)',
                            data: tempData.temp1,
                            borderColor: 'rgba(75, 192, 192, 1)',
                            backgroundColor: 'rgba(75, 192, 192, 0.2)',
                            tension: 0.1
                        },
                        {
                            label: 'Internal Temp (°C)',
                            data: tempData.temp2,
                            borderColor: 'rgba(255, 99, 132, 1)',
                            backgroundColor: 'rgba(255, 99, 132, 0.2)',
                            tension: 0.1
                        },
                        {
                            label: 'Target Temp (°C)',
                            data: tempData.labels.map(() => 0),
                            borderColor: 'rgba(54, 162, 235, 1)',
                            backgroundColor: 'rgba(54, 162, 235, 0.2)',
                            borderDash: [5, 5],
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    }
                }
            });
        }
        
        // Update chart with new data
        function updateChart(temp1, temp2, diff, target) {
            const now = new Date();
            const timeLabel = now.getHours() + ':' + now.getMinutes() + ':' + now.getSeconds();
            
            tempData.temp1.push(temp1);
            tempData.temp2.push(temp2);
            tempData.diff.push(diff);
            tempData.labels.push(timeLabel);
            
            if (tempData.temp1.length > maxDataPoints) {
                tempData.temp1.shift();
                tempData.temp2.shift();
                tempData.diff.shift();
                tempData.labels.shift();
            }
            
            // Update target temperature line
            tempChart.data.datasets[2].data = tempData.labels.map(() => target);
            
            tempChart.update();
        }
        
        // Update UI with status data
        function updateStatus(data) {
            document.getElementById('temp1').textContent = data.temp1.toFixed(1);
            document.getElementById('temp2').textContent = data.temp2.toFixed(1);
            document.getElementById('temp-diff').textContent = data.temp_diff.toFixed(1);
            document.getElementById('target-temp').textContent = data.target_temp.toFixed(1);
            document.getElementById('peltier-power').textContent = data.peltier_power;
            document.getElementById('current-mode').textContent = data.mode_name;
            document.getElementById('peltier-gauge').style.width = data.peltier_power + '%';
            
            // Update active mode button
            document.querySelectorAll('.btn').forEach(btn => btn.classList.remove('active'));
            if (data.mode === 0) document.getElementById('btn-off').classList.add('active');
            if (data.mode === 1) document.getElementById('btn-zip').classList.add('active');
            if (data.mode === 2) document.getElementById('btn-zap').classList.add('active');
            if (data.mode === 3) document.getElementById('btn-zoom').classList.add('active');
            
            // Update chart
            updateChart(data.temp1, data.temp2, data.temp_diff, data.target_temp);
            
            // Update system status
            document.getElementById('system-status').textContent = JSON.stringify(data, null, 2);
        }
        
        // Fetch status from server
        function fetchStatus() {
            fetch('/status')
                .then(response => response.json())
                .then(data => updateStatus(data))
                .catch(error => console.error('Error:', error));
        }
        
        // Set mode
        function setMode(mode) {
            fetch('/mode/' + mode)
                .then(response => response.json())
                .then(data => updateStatus(data))
                .catch(error => console.error('Error:', error));
        }
        
        // Initialize
        document.addEventListener('DOMContentLoaded', () => {
            initChart();
            fetchStatus();
            setInterval(fetchStatus, 2000);
        });
    </script>
</body>
</html>"""
    return html