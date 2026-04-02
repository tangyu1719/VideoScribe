import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const buttonVariants = cva(
  "inline-flex items-center justify-center whitespace-nowrap rounded-md text-sm font-medium ring-offset-background transition-all duration-200 ease-in-out focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring/50 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      variant: {
        default: "bg-primary text-primary-foreground hover:bg-primary/90 shadow-[0_1px_2px_0_rgb(0_0_0/_0.05)] hover:shadow-[0_4px_6px_-1px_rgb(0_0_0/_0.1),0_2px_4px_-2px_rgb(0_0_0/_0.1)] hover:-translate-y-0.5 active:translate-y-0 active:shadow-[0_1px_2px_0_rgb(0_0_0/_0.05)]",
        destructive: "bg-destructive text-destructive-foreground hover:bg-destructive/90 shadow-[0_1px_2px_0_rgb(0_0_0/_0.05)] hover:shadow-[0_4px_6px_-1px_rgb(0_0_0/_0.1),0_2px_4px_-2px_rgb(0_0_0/_0.1)] hover:-translate-y-0.5 active:translate-y-0",
        outline: "border border-input/50 bg-background/50 backdrop-blur-sm hover:bg-background/70 hover:border-muted-foreground/30 text-foreground shadow-[0_1px_2px_0_rgb(0_0_0/_0.05)] hover:shadow-[0_4px_6px_-1px_rgb(0_0_0/_0.1),0_2px_4px_-2px_rgb(0_0_0/_0.1)] hover:-translate-y-0.5 active:translate-y-0",
        secondary: "bg-secondary/80 backdrop-blur-sm text-secondary-foreground hover:bg-secondary shadow-[0_1px_2px_0_rgb(0_0_0/_0.05)] hover:shadow-[0_4px_6px_-1px_rgb(0_0_0/_0.1),0_2px_4px_-2px_rgb(0_0_0/_0.1)] hover:-translate-y-0.5 active:translate-y-0",
        ghost: "hover:bg-accent/50 hover:text-accent-foreground hover:-translate-y-0.5 transition-all duration-200",
        link: "text-primary underline-offset-4 hover:underline hover:-translate-y-0.5",
      },
      size: {
        default: "h-10 px-4 py-2",
        sm: "h-9 rounded-md px-3 text-xs",
        lg: "h-11 rounded-md px-8 text-base",
        icon: "h-10 w-10",
      },
    },
    defaultVariants: {
      variant: "default",
      size: "default",
    },
  }
)

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, ...props }, ref) => {
    const Comp = asChild ? Slot : "button"
    return (
      <Comp
        className={cn(buttonVariants({ variant, size, className }))}
        ref={ref}
        {...props}
      />
    )
  }
)
Button.displayName = "Button"

export { Button, buttonVariants }
