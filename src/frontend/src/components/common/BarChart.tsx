import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

type customBarChartType = {
  data: Record<string, string | number>[];
  xLabel: string;
  yLabel: string;
  dataKey: string;
  nameKey: string;
};

const CustomBarChart = ({ data, xLabel, yLabel, dataKey, nameKey }: customBarChartType) => {
  const [size, setSize] = useState({ width: 0, height: 0 });

  return (
    <ResponsiveContainer
      width="100%"
      height="100%"
      onResize={(containerWidth, containerHeight) => {
        setSize({ width: containerWidth, height: containerHeight });
      }}
    >
      <BarChart
        width={size.width}
        height={size.height}
        data={data}
        margin={{
          top: 5,
          right: 30,
          left: 20,
          bottom: 5,
        }}
        maxBarSize={50}
      >
        <XAxis
          dataKey={nameKey}
          style={{ fontSize: '12px' }}
          label={{
            value: `${xLabel}`,
            position: 'insideBottom',
            fontSize: '14px',
            offset: '-2',
          }}
        />
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
        <Tooltip cursor={{ fill: '#fcecd9' }} />
        <Bar dataKey={dataKey} fill="#F19C3C" radius={[5, 5, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
};

export default CustomBarChart;
