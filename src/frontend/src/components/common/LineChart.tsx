import React, { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

type customLineChartType = {
  data: Record<string, string | number>[];
  xAxisDataKey: string;
  lineOneKey: string;
  lineTwoKey: string;
  xLabel?: string;
  yLabel?: string;
};

const CustomLineChart = ({ data, xAxisDataKey, lineOneKey, lineTwoKey, xLabel, yLabel }: customLineChartType) => {
  const [size, setSize] = useState({ width: 0, height: 0 });

  return (
    <ResponsiveContainer
      width="100%"
      height="100%"
      onResize={(containerWidth, containerHeight) => {
        setSize({ width: containerWidth, height: containerHeight });
      }}
    >
      <LineChart
        width={size.width}
        height={size.height}
        data={data}
        margin={{
          right: 30,
          left: 20,
        }}
      >
        <CartesianGrid strokeDasharray="3 3" />
        {xLabel && (
          <XAxis
            style={{ fontSize: '12px' }}
            dataKey={xAxisDataKey}
            label={{
              value: `${xLabel}`,
              position: 'insideBottom',
              fontSize: '14px',
              offset: '1',
            }}
          />
        )}
        {yLabel && (
          <YAxis
            style={{ fontSize: '12px' }}
            label={{
              value: `${yLabel}`,
              angle: -90,
              fontSize: '14px',
              position: 'insideLeft',
              offset: '8',
              dy: 55,
            }}
          />
        )}
        <Tooltip />
        <Legend iconSize={10} iconType="circle" align="left" verticalAlign="top" height={45} />
        <Line dot={false} type="linear" dataKey={lineOneKey} stroke="#D73F3F" activeDot={{ r: 6 }} strokeWidth={1.5} />
        <Line dot={false} type="linear" dataKey={lineTwoKey} stroke="#F19C3C" activeDot={{ r: 6 }} strokeWidth={1.5} />
      </LineChart>
    </ResponsiveContainer>
  );
};

export default CustomLineChart;
