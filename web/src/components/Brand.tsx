import { Link } from 'react-router-dom'
import { Clock } from 'lucide-react'

export function Brand() {
    return (
        <Link to="/" className="flex items-center gap-2">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-slate-900">
                <Clock className="h-4 w-4 text-white" />
            </span>
            <span className="text-sm font-semibold tracking-tight text-slate-900">cronix</span>
        </Link>
    )
}
