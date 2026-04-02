import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"

const badgeVariants = cva(
  "inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-ring/50 focus:ring-offset-2 backdrop-blur-sm shadow-[0_1px_2px_0_rgb(0_0_0/_0.05)]",
  {
    variants: {
      variant: {
        default:
          "border-transparent bg-primary/90 text-primary-foreground hover:bg-primary hover:-translate-y-0.5",
        secondary:
          "border-transparent bg-secondary/80 text-secondary-foreground hover:bg-secondary hover:-translate-y-0.5",
        destructive:
          "border-transparent bg-destructive/90 text-destructive-foreground hover:bg-destructive hover:-translate-y-0.5",
        outline: "border-border/50 text-foreground hover:bg-background/50 hover:-translate-y-0.5",
      },
    },
    defaultVariants: {
      variant: "default",
    },
  }
)

export interface BadgeProps
  extends React.HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
