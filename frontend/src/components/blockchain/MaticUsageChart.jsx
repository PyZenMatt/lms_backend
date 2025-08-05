import React, { useState, useEffect } from 'react';
import { Card, Spinner, Form } from 'react-bootstrap';
import Chart from 'react-apexcharts';
import './MaticUsageChart.scss';

/**
 * Component to display MATIC usage over time in a chart
 */
const MaticUsageChart = ({ transactions }) => {
  const [loading, setLoading] = useState(true);
  const [chartData, setChartData] = useState(null);
  const [timeRange, setTimeRange] = useState('week'); // week, month, year

  useEffect(() => {
    if (!transactions) {
      return;
    }

    setLoading(true);

    // Process transaction data for chart
    const processChartData = () => {
      // Filter transactions to only include those that consumed MATIC (gas)
      const maticTransactions = transactions.filter(tx => 
        tx.gas_used && tx.status === 'confirmed'
      );

      // Determine date range based on selected time range
      const now = new Date();
      let startDate;
      let groupingFormat;
      let labelFormat;

      switch (timeRange) {
        case 'month':
          startDate = new Date(now);
          startDate.setMonth(now.getMonth() - 1);
          groupingFormat = 'day';
          labelFormat = date => `${date.getDate()}/${date.getMonth() + 1}`;
          break;
        case 'year':
          startDate = new Date(now);
          startDate.setFullYear(now.getFullYear() - 1);
          groupingFormat = 'month';
          labelFormat = date => {
            const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
            return months[date.getMonth()];
          };
          break;
        case 'week':
        default:
          startDate = new Date(now);
          startDate.setDate(now.getDate() - 7);
          groupingFormat = 'day';
          labelFormat = date => {
            const days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
            return days[date.getDay()];
          };
          break;
      }

      // Filter transactions by date range
      const filteredTransactions = maticTransactions.filter(tx => 
        new Date(tx.created_at) >= startDate
      );

      // Group transactions by date
      const groupedData = {};
      const categories = [];
      
      // Initialize categories and groupedData
      if (groupingFormat === 'day') {
        for (let i = 0; i < (timeRange === 'week' ? 7 : 30); i++) {
          const date = new Date(startDate);
          date.setDate(startDate.getDate() + i);
          const label = labelFormat(date);
          const dateKey = `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
          
          categories.push(label);
          groupedData[dateKey] = 0;
        }
      } else if (groupingFormat === 'month') {
        for (let i = 0; i < 12; i++) {
          const date = new Date(startDate);
          date.setMonth(startDate.getMonth() + i);
          const label = labelFormat(date);
          const dateKey = `${date.getFullYear()}-${date.getMonth() + 1}`;
          
          categories.push(label);
          groupedData[dateKey] = 0;
        }
      }

      // Sum gas used for each date group
      filteredTransactions.forEach(tx => {
        const txDate = new Date(tx.created_at);
        let dateKey;
        
        if (groupingFormat === 'day') {
          dateKey = `${txDate.getFullYear()}-${txDate.getMonth() + 1}-${txDate.getDate()}`;
        } else if (groupingFormat === 'month') {
          dateKey = `${txDate.getFullYear()}-${txDate.getMonth() + 1}`;
        }
        
        if (groupedData[dateKey] !== undefined) {
          // Convert gas used to MATIC (rough estimation)
          // This is a simplified calculation
          const gasPrice = tx.gas_price || 1; // Default to 1 if not provided
          const maticUsed = (tx.gas_used * gasPrice) / 1e18; // Convert to MATIC
          
          groupedData[dateKey] += maticUsed;
        }
      });

      // Convert grouped data to series
      const series = [
        {
          name: 'MATIC Used',
          data: Object.values(groupedData)
        }
      ];

      setChartData({
        series,
        categories
      });
      setLoading(false);
    };

    processChartData();
  }, [transactions, timeRange]);

  const handleTimeRangeChange = (e) => {
    setTimeRange(e.target.value);
  };

  // Chart options
  const chartOptions = {
    chart: {
      height: 350,
      type: 'area',
      toolbar: {
        show: false
      },
      zoom: {
        enabled: false
      }
    },
    dataLabels: {
      enabled: false
    },
    stroke: {
      curve: 'smooth',
      width: 2
    },
    fill: {
      type: 'gradient',
      gradient: {
        shadeIntensity: 1,
        opacityFrom: 0.7,
        opacityTo: 0.3,
        stops: [0, 90, 100]
      }
    },
    colors: ['#3b82f6'],
    xaxis: {
      categories: chartData?.categories || [],
      labels: {
        style: {
          fontSize: '12px',
          fontFamily: 'Helvetica, Arial, sans-serif',
        }
      }
    },
    yaxis: {
      title: {
        text: 'MATIC Used'
      },
      labels: {
        formatter: function(value) {
          return value.toFixed(6);
        }
      }
    },
    tooltip: {
      y: {
        formatter: function(value) {
          return value.toFixed(6) + ' MATIC';
        }
      }
    }
  };

  return (
    <Card className="matic-usage-chart">
      <Card.Header className="d-flex justify-content-between align-items-center">
        <Card.Title as="h5">
          <i className="feather icon-trending-up mr-2"></i>
          MATIC Consumption
        </Card.Title>
        <Form.Select
          className="time-range-select"
          value={timeRange}
          onChange={handleTimeRangeChange}
          style={{ width: '120px' }}
        >
          <option value="week">Last Week</option>
          <option value="month">Last Month</option>
          <option value="year">Last Year</option>
        </Form.Select>
      </Card.Header>
      <Card.Body>
        {loading ? (
          <div className="text-center py-5">
            <Spinner animation="border" variant="primary" />
            <p className="mt-3 text-muted">Loading chart data...</p>
          </div>
        ) : chartData && chartData.series[0].data.every(val => val === 0) ? (
          <div className="text-center py-5">
            <i className="feather icon-bar-chart-2 no-data-icon"></i>
            <p className="mt-3 text-muted">No MATIC usage data available for the selected period</p>
          </div>
        ) : chartData && (
          <Chart
            options={chartOptions}
            series={chartData.series}
            type="area"
            height={350}
          />
        )}
      </Card.Body>
    </Card>
  );
};

export default MaticUsageChart;
