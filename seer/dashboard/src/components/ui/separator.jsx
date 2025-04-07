import React from "react";
import cn from "classnames";

const Separator = ({ 
  className, 
  orientation = "horizontal", 
  decorative = true, 
  ...props 
}) => {
  return (
    <div
      role={decorative ? "presentation" : "separator"}
      aria-orientation={orientation}
      className={cn(
        "shrink-0 bg-border",
        orientation === "horizontal" ? "h-[1px] w-full" : "h-full w-[1px]",
        className
      )}
      {...props}
    />
  );
};

export { Separator }; 