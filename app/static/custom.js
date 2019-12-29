/**
 * downloadChart starts a png download of a chart.js chart given its canvas elementID.
 * @param {string} elementID - string ID of the element to insert the chart within.
 */
function downloadChart(elementID) {
    var url = document.getElementById(elementID).toDataURL('image/png');

    // there MUST be a better way to do this
    var a = document.createElement('a');
    a.href = url;
    a.download = "chart.png";
    a.click()
    a.remove()
}

/**
 * createChart inserts a chart.js chart into an elementID, returning the chart variable.
 * @param {string} elementID - string ID of the element to insert the chart within.
 * @param {Array.Number} fahrenheit - Temperature readings, in Fahrenheit.
 * @param {Array.Date} datetimes - Datetime of each of the Fahrenheit reading.
 * @param {Array.Number} [requirements] - Optional required temperature per nyc regulation.
 */
function createChart(elementID, fahrenheit, datetimes, requirements) {
    var datasets = [{
        data: fahrenheit,
        label: "Degrees Fahrenheit",
        borderColor: "#c45850",
        borderWidth: 3,
        pointRadius: 0,
    }];

    var options = {
        tooltips: { enabled: true },
        legend: { display: false },
        scales: {
            xAxes: [{
                type: 'time',
                time: { tooltipFormat: 'LT', },
                ticks: {},
            }],
            yAxes: [{
                ticks: {
                    max: Math.ceil(Math.max(73, Math.max.apply(null, fahrenheit) * 1.05)),
                    min: Math.floor(Math.min(60, Math.min.apply(null, fahrenheit) * 0.95)),
                },
                scaleLabel: { display: false, labelString: 'Degrees Fahrenheit' }
            }]
        },
    }

    if (reqs !== undefined) {
        datasets.push({
            data: requirements,
            label: "Minimum Required Temperature",
            borderColor: 'rgba(0, 0, 0, 0.1)',
            fill: false,
            borderDash: [10, 5],
            pointRadius: 0,
        });
    };

    chart = new Chart(document.getElementById(elementID), {
        type: 'line',
        data: { labels: datetimes, datasets: datasets },
        options: options
    });

    // add download shortcut when chart is ready
    chart.options.animation.onComplete = function () {
        chart.download = function () { downloadChart(elementID) }
    };
    return chart
};

