import React from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

type DateRangePickerType = {
  title: string;
  className: string;
  setStartDate: (date: Date | null) => void;
  setEndDate: (date: Date | null) => void;
  startDate: Date | null;
  endDate: Date | null;
};

const DateRangePicker = ({ title, className, setStartDate, setEndDate, startDate, endDate }: DateRangePickerType) => {
  const onChange = (dates: [Date | null, Date | null]) => {
    const [start, end] = dates;
    setStartDate(start);
    setEndDate(end);
  };
  return (
    <div className="fmtm-z-[10000] fmtm-w-full">
      {title && (
        <p className={`fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold !fmtm-bg-transparent ${className}`}>{title}</p>
      )}
      <DatePicker
        selected={startDate}
        onChange={onChange}
        startDate={startDate}
        endDate={endDate}
        selectsRange
        className="fmtm-outline-none fmtm-border-[1px] fmtm-border-gray-300 fmtm-h-[2rem] fmtm-w-full fmtm-z-50 fmtm-px-2 fmtm-text-base fmtm-pt-1 hover"
        placeholderText="YYYY/MM/DD"
        dateFormat="yyyy/MM/dd"
      />
    </div>
  );
};

export default DateRangePicker;
