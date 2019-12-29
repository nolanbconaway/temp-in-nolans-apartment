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
 * downloadCSV creates CSV data diven dates, temps and requirements, then downloads the data.
 * @param {Array.Date} datetimes - Datetime of each of the Fahrenheit reading.
 * @param {Array.Number} fahrenheit - Temperature readings, in Fahrenheit.
 * @param {Array.Number} [requirements] - Optional required temperature per nyc regulation.
 */
function downloadCSV(datetimes, fahrenheit, requirements) {
    if (requirements !== undefined) {
        var headers = '\ndatetime\tfahrenheit\trequirement\n'
        var zipped = datetimes.map(function (e, i) {
            return [e, fahrenheit[i], requirements[i]];
        });
    } else {
        var headers = '\ndttm\tfahrenheit\n'
        var zipped = datetimes.map(function (e, i) {
            return [e, fahrenheit[i]];
        });
    }

    var tsv = headers + zipped.map(function (d) {
        return d.join('\t');
    }).join('\n');

    // there MUST be a better way to do this
    var a = document.createElement("a");
    var blob = new Blob([tsv], { type: 'text/csv;charset=utf-8;' });
    var url = URL.createObjectURL(blob);
    a.href = url;
    a.download = "chart.csv";
    a.click();
    a.remove();
}

/**
 * createChart inserts a chart.js chart into an elementID, returning the chart variable.
 * @param {string} elementID - string ID of the element to insert the chart within.
 * @param {Array.Date} datetimes - Datetime of each of the Fahrenheit reading.
 * @param {Array.Number} fahrenheit - Temperature readings, in Fahrenheit.
 * @param {Array.Number} [requirements] - Optional required temperature per nyc regulation.
 */
function createChart(elementID, datetimes, fahrenheit, requirements) {
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

    var chart = new Chart(document.getElementById(elementID), {
        type: 'line',
        data: { labels: datetimes, datasets: datasets },
        options: options
    });

    // add download csv shortcut
    chart.downloadCSV = function () {
        downloadCSV(datetimes, fahrenheit, requirements)
    }

    // add download shortcut when chart is ready
    chart.options.animation.onComplete = function () {
        chart.downloadPNG = function () { downloadChart(elementID) }
    };

    return chart
};

