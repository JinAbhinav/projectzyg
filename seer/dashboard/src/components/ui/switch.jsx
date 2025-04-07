import React from "react";
import cn from "classnames";

const Switch = React.forwardRef(({ className, checked, onCheckedChange, disabled, ...props }, ref) => {
  const [isChecked, setIsChecked] = React.useState(checked || false);
  
  React.useEffect(() => {
    if (checked !== undefined) {
      setIsChecked(checked);
    }
  }, [checked]);
  
  const handleChange = (e) => {
    const newValue = e.target.checked;
    setIsChecked(newValue);
    if (onCheckedChange) {
      onCheckedChange(newValue);
    }
  };
  
  return (
    <label className={cn("inline-flex items-center", disabled && "cursor-not-allowed opacity-50", className)}>
      <input
        type="checkbox"
        className="sr-only"
        checked={isChecked}
        onChange={handleChange}
        disabled={disabled}
        ref={ref}
        {...props}
      />
      <div
        aria-hidden="true"
        className={cn(
          "relative h-6 w-11 cursor-pointer rounded-full transition-colors",
          isChecked ? "bg-primary" : "bg-input",
          disabled && "cursor-not-allowed"
        )}
      >
        <div
          className={cn(
            "absolute top-1 h-4 w-4 rounded-full bg-background transition-transform",
            isChecked ? "translate-x-6" : "translate-x-1"
          )}
        />
      </div>
    </label>
  );
});

Switch.displayName = "Switch";

export { Switch }; 