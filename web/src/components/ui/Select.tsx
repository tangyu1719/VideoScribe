import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

interface SelectOption {
  value: string
  label: string
}

interface SelectProps extends Omit<React.SelectHTMLAttributes<HTMLSelectElement>, 'onChange'> {
  options: SelectOption[]
  onValueChange?: (value: string) => void
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, options, onValueChange, ...props }, ref) => {
    return (
      <div className="relative">
        <select
          className={cn(
            "flex h-10 w-full appearance-none rounded-md border border-input/50 bg-background/50 backdrop-blur-sm px-3 py-2 text-sm ring-offset-background focus-visible:bg-background/80 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-0",
            "transition-all duration-200 ease-in-out",
            "hover:bg-background/70 hover:border-muted-foreground/30",
            "disabled:cursor-not-allowed disabled:opacity-50 pr-10",
            className
          )}
          ref={ref}
          onChange={(e) => onValueChange?.(e.target.value)}
          {...props}
        >
          {options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <ChevronDown className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground/70 pointer-events-none" />
      </div>
    )
  }
)
Select.displayName = "Select"

export { Select }
