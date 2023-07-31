myChart1 = echarts.init(document.getElementById("chart1"));
myChart2 = echarts.init(document.getElementById("chart2"));
myChart3 = echarts.init(document.getElementById("chart3"));
myChart4 = echarts.init(document.getElementById("chart4"));

option1 = {
    tooltip: {
        formatter: '{a} <br/>{b} : {c}%'
    },
    toolbox: {
        feature: {
            // restore: {},
            // saveAsImage: {}
        }
    },
    series: [
        {
            name: '节点状态',
            type: 'gauge',
            splitNumber: 5,  // 刻度切几个
            radius: '90%',   // 图形大小
            title:{
                show:true,
                offsetCenter: [0, '90%'],
                color:'#2F4056',
                fontSize:13,
                fontWeight: 'bold',
                backgroundColor: '#FFF',
                borderRadius:18,
                padding: 6,
                shadowColor:"#C3Cfff",
                shadowBlur:6,
            },
            pointer: {
                width:5,//指针的宽度
                length:"40%", //指针长度，按照半圆半径的百分比
                shadowColor : '#ccc', //默认透明
                shadowBlur: 5
            },
            markPoint:{
                symbol:'circle',
                symbolSize:3,
                //在指针上添加一个白点
                data:[{x:'center',y:'center',itemStyle:{color:'#FFF'}}]
            },
            axisLabel: {            // 坐标轴小标记
                textStyle: {       // 属性lineStyle控制线条样式
                    color: '#000',
                    fontSize: 9,   //改变仪表盘内刻度数字的大小
                    shadowColor: '#000', //默认透明
                }
            },
            axisLine: {            // 坐标轴线
                lineStyle: {       // 属性lineStyle控制线条样式
                    color: [[0.2, '#D94600'],[0.8,'#000079'],[1,'#009393']],
                    width: 10,
                    shadowColor: '#000', //默认透明
                    shadowBlur: 0,
                }
            },
            detail: {
                formatter: '{value}%',
                fontSize: 16,
            },
            data: [{value: 50, name: '节点状态'}]
        }
    ]
};
option2 = {
    tooltip: {
        formatter: '{a} <br/>{b} : {c}%'
    },
    toolbox: {
        feature: {
            // restore: {},
            // saveAsImage: {}
        }
    },
    series: [
        {
            name: '节点调度',
            type: 'gauge',
            splitNumber: 5,  // 刻度切几个
            radius: '90%',   // 图形大小
            title:{
                show:true,
                offsetCenter: [0, '90%'],
                color:'#2F4056',
                fontSize:13,
                fontWeight: 'bold',
                backgroundColor: '#FFF',
                borderRadius:18,
                padding: 6,
                shadowColor:"#C3Cfff",
                shadowBlur:6,
            },
            pointer: {
                width:5,//指针的宽度
                length:"40%", //指针长度，按照半圆半径的百分比
                shadowColor : '#ccc', //默认透明
                shadowBlur: 5
            },
            markPoint:{
                symbol:'circle',
                symbolSize:3,
                //在指针上添加一个白点
                data:[{x:'center',y:'center',itemStyle:{color:'#FFF'}}]
            },
            axisLabel: {            // 坐标轴小标记
                textStyle: {       // 属性lineStyle控制线条样式
                    color: '#000',
                    fontSize: 9,   //改变仪表盘内刻度数字的大小
                    shadowColor: '#000', //默认透明
                }
            },
            axisLine: {            // 坐标轴线
                lineStyle: {       // 属性lineStyle控制线条样式
                    color: [[0.2, '#D94600'],[0.8,'#000079'],[1,'#009393']],
                    width: 10,
                    shadowColor: '#000', //默认透明
                    shadowBlur: 0,
                }
            },
            detail: {
                formatter: '{value}%',
                fontSize: 16
            },
            data: [{value: 50, name: '节点调度'}]
        }
    ]
};
option3 = {
    tooltip: {
        formatter: '{a} <br/>{b} : {c}%'
    },
    toolbox: {
        feature: {
            // restore: {},
            // saveAsImage: {}
        }
    },
    series: [
        {
            name: 'CPU',
            type: 'gauge',
            splitNumber: 5,  // 刻度切几个
            radius: '90%',   // 图形大小
            title:{
                show:true,
                offsetCenter: [0, '90%'],
                color:'#2F4056',
                fontSize:13,
                fontWeight: 'bold',
                backgroundColor: '#FFF',
                borderRadius:18,
                padding: 6,
                shadowColor:"#C3Cfff",
                shadowBlur:6,
            },
            pointer: {
                width:5,//指针的宽度
                length:"40%", //指针长度，按照半圆半径的百分比
                shadowColor : '#ccc', //默认透明
                shadowBlur: 5
            },
            markPoint:{
                symbol:'circle',
                symbolSize:3,
                //在指针上添加一个白点
                data:[{x:'center',y:'center',itemStyle:{color:'#FFF'}}]
            },
            axisLabel: {            // 坐标轴小标记
                textStyle: {       // 属性lineStyle控制线条样式
                    color: '#000',
                    fontSize: 9,   //改变仪表盘内刻度数字的大小
                    shadowColor: '#000', //默认透明
                }
            },
            axisLine: {            // 坐标轴线
                lineStyle: {       // 属性lineStyle控制线条样式
                    color: [[0.2, '#009393'], [0.8, '#000079'], [1, '#D94600']],
                    width: 10,
                    shadowColor: '#000', //默认透明
                    shadowBlur: 0,
                }
            },
            detail: {
                formatter: '{value}%',
                fontSize: 16,
            },
            data: [{value: 50, name: 'CPU使用量'}]
        }
    ]
};
option4 = {
    tooltip: {
        formatter: '{a} <br/>{b} : {c}%',
    },
    toolbox: {
        feature: {
            // restore: {},
            // saveAsImage: {}
        }
    },
    series: [
        {
            name: '内存',
            type: 'gauge',
            splitNumber: 5,  // 刻度切几个
            radius: '90%',   // 图形大小
            title:{
                show:true,
                offsetCenter: [0, '90%'],
                color:'#2F4056',
                fontSize:13,
                fontWeight: 'bold',
                backgroundColor: '#FFF',
                borderRadius:18,
                padding: 6,
                shadowColor:"#C3Cfff",
                shadowBlur:6,
            },
            pointer: {
                width:5,//指针的宽度
                length:"40%", //指针长度，按照半圆半径的百分比
                shadowColor : '#ccc', //默认透明
                shadowBlur: 5
            },
            markPoint:{
                symbol:'circle',
                symbolSize:3,
                //在指针上添加一个白点
                data:[{x:'center',y:'center',itemStyle:{color:'#FFF'}}]
            },
            axisLabel: {            // 坐标轴小标记
                textStyle: {       // 属性lineStyle控制线条样式
                    color: '#000',
                    fontSize: 9,   //改变仪表盘内刻度数字的大小
                    shadowColor: '#000', //默认透明
                }
            },
            axisLine: {            // 坐标轴线
                lineStyle: {       // 属性lineStyle控制线条样式
                    color: [[0.2, '#009393'], [0.8, '#000079'], [1, '#D94600']],
                    width: 10,
                    shadowColor: '#000', //默认透明
                    shadowBlur: 0,
                }
            },
            detail: {
                formatter: '{value}%',
                fontSize: 16,
            },
            data: [{value: 50, name: '内存使用量'}],
        }
    ]
};

myChart1.setOption(option1, true);
myChart2.setOption(option2, true);
myChart3.setOption(option3, true);
myChart4.setOption(option4, true);
