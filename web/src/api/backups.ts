import { api } from './client'
import type {
    BackupCreateResult,
    BackupInfo,
    BackupRestoreResult,
    BackupUploadResult,
    KryvaBackupInfo,
    Page,
} from './types'

interface RestoreAuth {
    password: string
    code?: string
}

export function listBackups(): Promise<BackupInfo[]> {
    return api.get<BackupInfo[]>('/api/v1/backups')
}

export function listKryvaBackups(page = 1, pageSize = 20): Promise<Page<KryvaBackupInfo>> {
    return api.get<Page<KryvaBackupInfo>>(
        `/api/v1/backups/kryva?page=${page}&page_size=${pageSize}`,
    )
}

export function createBackup(upload: boolean): Promise<BackupCreateResult> {
    return api.post<BackupCreateResult>('/api/v1/backups', { upload })
}

export function uploadBackup(filename: string): Promise<BackupUploadResult> {
    return api.post<BackupUploadResult>(
        `/api/v1/backups/${encodeURIComponent(filename)}/upload`,
    )
}

export function restoreBackup(
    filename: string,
    auth: RestoreAuth,
): Promise<BackupRestoreResult> {
    return api.post<BackupRestoreResult>(
        `/api/v1/backups/${encodeURIComponent(filename)}/restore`,
        auth,
    )
}

export function restoreRemoteBackup(
    filename: string,
    auth: RestoreAuth,
): Promise<BackupRestoreResult> {
    return api.post<BackupRestoreResult>('/api/v1/backups/restore-remote', {
        filename,
        ...auth,
    })
}

export function deleteBackup(filename: string): Promise<boolean> {
    return api.delete<boolean>(`/api/v1/backups/${encodeURIComponent(filename)}`)
}
