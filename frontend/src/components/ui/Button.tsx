import React from 'react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'default' | 'destructive' | 'outline' | 'secondary' | 'ghost' | 'link';
  size?: 'default' | 'sm' | 'lg' | 'icon';
  children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({ 
  variant = 'default', 
  size = 'default', 
  className = '', 
  children, 
  ...props 
}) => {
  const baseClasses = 'inline-flex items-center justify-center whitespace-nowrap rounded-lg text-sm font-semibold ring-offset-white transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-950 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 shadow-sm hover:shadow-md';
  
  const variantClasses = {
    default: 'bg-slate-900 text-slate-50 hover:bg-slate-800 border border-slate-900',
    destructive: 'bg-red-500 text-slate-50 hover:bg-red-600 border border-red-500',
    outline: 'border border-slate-300 bg-white hover:bg-slate-50 hover:text-slate-900 text-slate-700',
    secondary: 'bg-slate-100 text-slate-900 hover:bg-slate-200 border border-slate-200',
    ghost: 'hover:bg-slate-100 hover:text-slate-900 text-slate-700',
    link: 'text-slate-900 underline-offset-4 hover:underline shadow-none'
  };
  
  const sizeClasses = {
    default: 'h-11 px-6 py-2',
    sm: 'h-9 rounded-lg px-4',
    lg: 'h-12 rounded-lg px-8',
    icon: 'h-11 w-11'
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};