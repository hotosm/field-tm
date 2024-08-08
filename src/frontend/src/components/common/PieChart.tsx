import React, { useState } from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';

type customPieChartType = {
  data: Record<string, string | number>[];
  dataKey: string;
  nameKey: string;
};

const COLORS = ['#F19C3C', '#D73F3F', '#FFB74D', '#EC407A'];

const RADIAN = Math.PI / 180;

const renderCustomizedLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent, index }) => {
  const radius = innerRadius + (outerRadius - innerRadius) * 1.4;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);

  return (
    <text x={x} y={y} fill={COLORS[index]} textAnchor={x > cx ? 'start' : 'end'} dominantBaseline="central">
      {`${(percent * 100).toFixed(0)}%`}
    </text>
  );
};

const renderColorfulLegendText = (value: string, entry: any) => (
  <span style={{ color: '#596579', fontWeight: 500, padding: '10px' }}>{value}</span>
);

const CustomLegend = ({ payload }) => (
  <div
    className={`fmtm-gap-x-6 fmtm-grid fmtm-grid-cols-auto fmtm-min-w-[100px] ${
      // eslint-disable-next-line no-nested-ternary
      payload.length > 6 ? 'fmtm-grid-cols-3' : payload.length > 3 ? 'fmtm-grid-cols-2' : ''
    }`}
  >
    {payload.map((entry, index) => (
      <div className="fmtm-flex fmtm-items-center fmtm-gap-2" key={index}>
        <div
          style={{ backgroundColor: entry.color }}
          className="fmtm-w-[10px] fmtm-h-[10px] fmtm-min-w-3 fmtm-min-h-3 fmtm-rounded-full"
        />
        <p
          className="fmtm-capitalize fmtm-truncate fmtm-text-base"
          title={`${entry.value} - ${(entry.payload.percent * 100).toFixed(0)}%`}
        >
          {entry.value} - {(entry.payload.percent * 100).toFixed(0)}%
        </p>
      </div>
    ))}
  </div>
);

const CustomPieChart = ({ data, dataKey, nameKey }: customPieChartType) => {
  const [size, setSize] = useState({ width: 0, height: 0 });

  return (
    <ResponsiveContainer
      width="100%"
      height="105%"
      onResize={(containerWidth, containerHeight) => {
        setSize({ width: containerWidth, height: containerHeight });
      }}
    >
      <PieChart width={size.width} height={size.height}>
        <Pie
          data={data}
          cx="50%"
          cy="50%"
          innerRadius={60}
          outerRadius={110}
          fill="#8884d8"
          paddingAngle={0}
          dataKey={dataKey}
          nameKey={nameKey}
        >
          {data.map((entry, index) => (
            <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip />
        <Legend
          iconType="circle"
          layout="vertical"
          verticalAlign="bottom"
          iconSize={10}
          formatter={renderColorfulLegendText}
          content={<CustomLegend payload={data?.map((_, index) => COLORS[index % COLORS.length])} />}
        />
      </PieChart>
    </ResponsiveContainer>
  );
};

export default CustomPieChart;
