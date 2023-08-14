const ctx = document.getElementById('lineChart').getContext('2d');
const myChart = new Chart(ctx, {
    type: 'lineChart',
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
        scales: {
            y: {
                beginAtZero: true
            }
        }
    }
});






// const ctx = document.getElementById('lineChart').getContext('2d');
// const myChart = new Chart(ctx, {
    // type: 'line',
    data: {
        // labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun','Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'],
        datasets: [{
            // label: 'Earning in $',
            // data: [2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022],
            // backgroundColor: [
                // 'rgba(338, 42, 49, 0.1)',
                // 'rgba(54, 162, 235, 0.2)',
                // 'rgba(255, 206, 86, 0.2)',
                // 'rgba(75, 192, 192, 0.2)',
                // 'rgba(153, 102, 255, 0.2)',
                // 'rgba(255, 159, 64, 0.2)'
                
            ],
            // borderColor: [
//                 'rgba(54, 162, 235, 1)',
//                 'rgba(255, 206, 86, 1)',
//                 'rgba(75, 192, 192, 1)',
//                 'rgba(153, 102, 255, 1)',
//                 'rgba(255, 159, 64, 1)'
//             ],
//             borderWidth: 1
//         }]
//     },
//     options: {
//        responsive: true
//     }
// });

