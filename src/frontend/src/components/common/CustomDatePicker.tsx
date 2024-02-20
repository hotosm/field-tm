import React from 'react';
import DatePicker from 'react-datepicker';
import 'react-datepicker/dist/react-datepicker.css';

type CustomDatePickerType = {
  title: string;
  className: string;
  selectedDate: string | null;
  setSelectedDate: (date: Date) => void;
};

const CustomDatePicker = ({ title, className, selectedDate, setSelectedDate }: CustomDatePickerType) => {
  return (
    <div className="fmtm-z-[10000] fmtm-w-full">
      {title && (
        <p className={`fmtm-text-[1rem] fmtm-mb-2 fmtm-font-semibold !fmtm-bg-transparent ${className}`}>{title}</p>
      )}
      <DatePicker
        selected={selectedDate}
        onChange={(date) => setSelectedDate(date)}
        className="fmtm-outline-none fmtm-border-[1px] fmtm-border-gray-300 fmtm-h-[2rem] fmtm-w-full fmtm-z-50 fmtm-px-2 fmtm-text-base fmtm-pt-1 hover"
        placeholderText="YYYY/MM/DD"
        dateFormat="yyyy/MM/dd"
      />
    </div>
  );
};

export default CustomDatePicker;
