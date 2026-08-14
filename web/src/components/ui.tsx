import type { ButtonHTMLAttributes, HTMLAttributes, ReactNode } from "react";
import { Slider as SliderPrimitive, Switch as SwitchPrimitive } from "radix-ui";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "../lib/utils";

const buttonVariants = cva("button", {
  variants: {
    variant: {
      primary: "button--primary",
      secondary: "button--secondary",
      ghost: "button--ghost",
    },
    size: {
      default: "button--default",
      small: "button--small",
      icon: "button--icon",
    },
  },
  defaultVariants: {
    variant: "primary",
    size: "default",
  },
});

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> &
  VariantProps<typeof buttonVariants>;

export function Button({ className, variant, size, ...props }: ButtonProps) {
  return (
    <button
      className={cn(buttonVariants({ variant, size }), className)}
      {...props}
    />
  );
}

type BadgeProps = HTMLAttributes<HTMLSpanElement> & {
  tone?: "neutral" | "accent" | "success" | "warm";
};

export function Badge({ className, tone = "neutral", ...props }: BadgeProps) {
  return <span className={cn("badge", `badge--${tone}`, className)} {...props} />;
}

export function Switch({
  checked,
  onCheckedChange,
  label,
}: {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  label: string;
}) {
  return (
    <SwitchPrimitive.Root
      checked={checked}
      className="switch"
      onCheckedChange={onCheckedChange}
      aria-label={label}
    >
      <SwitchPrimitive.Thumb className="switch__thumb" />
    </SwitchPrimitive.Root>
  );
}

export function Slider({
  value,
  onValueChange,
  label,
}: {
  value: number;
  onValueChange: (value: number) => void;
  label: string;
}) {
  return (
    <SliderPrimitive.Root
      className="slider"
      value={[value]}
      min={0}
      max={100}
      step={1}
      onValueChange={([nextValue]) => onValueChange(nextValue)}
      aria-label={label}
    >
      <SliderPrimitive.Track className="slider__track">
        <SliderPrimitive.Range className="slider__range" />
      </SliderPrimitive.Track>
      <SliderPrimitive.Thumb className="slider__thumb" aria-label={label} />
    </SliderPrimitive.Root>
  );
}

export function SectionHeader({
  eyebrow,
  title,
  action,
}: {
  eyebrow: string;
  title: string;
  action?: ReactNode;
}) {
  return (
    <div className="section-header">
      <div>
        <p className="eyebrow">{eyebrow}</p>
        <h2>{title}</h2>
      </div>
      {action}
    </div>
  );
}
