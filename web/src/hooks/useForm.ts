import { useState } from 'react'

/**
 * 通用表单状态管理 Hook
 */
export function useForm<T extends Record<string, any>>(initialValues: T) {
    const [values, setValues] = useState<T>(initialValues)
    const [errors, setErrors] = useState<Partial<Record<keyof T, boolean>>>({})
    const [loading, setLoading] = useState(false)

    const updateValue = (key: keyof T, value: any) => {
        setValues((prev) => ({ ...prev, [key]: value }))
        if (errors[key]) {
            setErrors((prev) => ({ ...prev, [key]: false }))
        }
    }

    const updateValues = (newValues: Partial<T>) => {
        setValues((prev) => ({ ...prev, ...newValues }))
    }

    const reset = (newValues?: T) => {
        setValues(newValues || initialValues)
        setErrors({})
    }

    const validate = (rules: Partial<Record<keyof T, (value: any) => boolean>>) => {
        const newErrors: Partial<Record<keyof T, boolean>> = {}
        let isValid = true

        Object.entries(rules).forEach(([key, validator]) => {
            if (!validator(values[key as keyof T])) {
                newErrors[key as keyof T] = true
                isValid = false
            }
        })

        setErrors(newErrors)
        return isValid
    }

    return {
        values,
        errors,
        loading,
        setLoading,
        updateValue,
        updateValues,
        reset,
        validate,
    }
}
