import { InputHTMLAttributes, forwardRef } from 'react'
import clsx from 'clsx'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-sm text-gray-400 mb-1.5">{label}</label>
        )}
        <input
          ref={ref}
          className={clsx(
            'input-field',
            error && 'border-signal-red',
            className
          )}
          {...props}
        />
        {error && (
          <p className="mt-1 text-sm text-signal-red">{error}</p>
        )}
      </div>
    )
  }
)

Input.displayName = 'Input'

export default Input