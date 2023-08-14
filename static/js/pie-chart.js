const ctx = document.getElementById('doughnut').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'doughnut',
    data: {
        labels: ['Totla Sale', 'Total Referral', 'Total Affiliate', 'Total Earn'],
        datasets: [{
            label: 'Afiliate',
            data: [42, 29, 8, 6,],
            backgroundColor: [
                'rgba(70, 145, 206, 1)',
                'rgba(250, 213, 329, 1)',
                'rgba(238, 44, 52, 1)',
                'rgba(153, 102, 255, 1)',
                'rgba(255, 159, 64, 1)'
                
            ],
            borderColor: [
                'rgba(255, 99, 132, 1)'
            ],
            borderWidth: 1
        }]
    },
    options: {
        responsive: true
    }
});