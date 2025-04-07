import React from "react";
import cn from "classnames";

const variantStyles = {
  default: "bg-background text-foreground",
  destructive: "border-destructive/50 text-destructive dark:border-destructive [&>svg]:text-destructive",
};

const Alert = ({ className, variant = "default", ...props }) => {
  return (
    <div
      role="alert"
      className={cn(
        "relative w-full rounded-lg border p-4 [&>svg+div]:translate-y-[-3px] [&>svg]:absolute [&>svg]:left-4 [&>svg]:top-4 [&>svg]:text-foreground [&>svg~*]:pl-7",
        variantStyles[variant],
        className
      )}
      {...props}
    />
  );
};

const AlertTitle = ({ className, ...props }) => {
  return (
    <h5
      className={cn("mb-1 font-medium leading-none tracking-tight", className)}
      {...props}
    />
  );
};

const AlertDescription = ({ className, ...props }) => {
  return (
    <div
      className={cn("text-sm [&_p]:leading-relaxed", className)}
      {...props}
    />
  );
};

export { Alert, AlertTitle, AlertDescription }; 