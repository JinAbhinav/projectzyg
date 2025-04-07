import React, { useState, useEffect, useRef } from "react";
import cn from "classnames";

const Slider = ({
  className,
  min = 0,
  max = 100,
  step = 1,
  value = [0],
  onValueChange,
  disabled = false,
  ...props
}) => {
  const [values, setValues] = useState(value);
  const trackRef = useRef(null);
  
  useEffect(() => {
    setValues(value);
  }, [value]);
  
  const handlePointerDown = (event) => {
    if (disabled) return;
    
    const track = trackRef.current;
    if (!track) return;
    
    const { left, width } = track.getBoundingClientRect();
    const clientX = event.clientX;
    const percentage = (clientX - left) / width;
    const newValue = min + Math.round((max - min) * percentage / step) * step;
    const clampedValue = Math.max(min, Math.min(max, newValue));
    
    const newValues = [...values];
    newValues[0] = clampedValue;
    
    setValues(newValues);
    if (onValueChange) onValueChange(newValues);
  };
  
  const getThumbStyle = (val) => {
    const percentage = ((val - min) / (max - min)) * 100;
    return {
      left: `${percentage}%`,
      transform: 'translateX(-50%)'
    };
  };
  
  const getRangeStyle = () => {
    const percentage = ((values[0] - min) / (max - min)) * 100;
    return {
      width: `${percentage}%`
    };
  };
  
  return (
    <div
      className={cn("relative flex w-full touch-none select-none items-center", className)}
      {...props}
    >
      <div
        ref={trackRef}
        className="relative h-2 w-full grow rounded-full bg-secondary"
        onPointerDown={handlePointerDown}
      >
        <div
          className="absolute h-full rounded-full bg-primary"
          style={getRangeStyle()}
        />
        {values.map((val, index) => (
          <div
            key={index}
            className="absolute top-1/2 h-4 w-4 rounded-full border-2 border-primary bg-background ring-offset-background transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:pointer-events-none disabled:opacity-50"
            style={getThumbStyle(val)}
          />
        ))}
      </div>
    </div>
  );
};

export { Slider }; 