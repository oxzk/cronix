import { useState, useEffect } from 'react'

interface PaginationParams {
    page?: number
    page_size?: number
    [key: string]: any
}

interface PaginationResult<T> {
    items: T[]
    total: number
    page: number
    page_size: number
    total_pages: number
}

/**
 * 通用分页数据加载 Hook
 */
export function usePagination<T>(
    fetchFn: (params: PaginationParams) => Promise<PaginationResult<T>>,
    pageSize = 20,
    filters: Record<string, any> = {},
) {
    const [data, setData] = useState<T[]>([])
    const [loading, setLoading] = useState(true)
    const [currentPage, setCurrentPage] = useState(1)
    const [totalPages, setTotalPages] = useState(1)

    useEffect(() => {
        const loadData = async () => {
            try {
                setLoading(true)
                const params: PaginationParams = { page: currentPage, page_size: pageSize, ...filters }
                const response = await fetchFn(params)
                setData(response.items || [])
                setTotalPages(response.total_pages || 1)
            } catch (error) {
                console.error('Failed to load data:', error)
                setData([])
                setTotalPages(1)
            } finally {
                setLoading(false)
            }
        }

        loadData()
    }, [currentPage, pageSize, JSON.stringify(filters)])

    return {
        data,
        loading,
        currentPage,
        totalPages,
        setCurrentPage,
        reload: () => setCurrentPage((prev) => prev), // 触发重新加载
    }
}
