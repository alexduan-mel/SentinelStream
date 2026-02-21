from __future__ import annotations

from uuid import UUID


def publish_job(conn, news_id: str, trace_id: UUID, job_type: str = "llm_analysis") -> bool:
    sql = (
        "INSERT INTO analysis_jobs (news_id, trace_id, job_type, status) "
        "VALUES (%s, %s, %s, 'pending') "
        "ON CONFLICT (news_id, job_type) DO NOTHING "
        "RETURNING 1"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (news_id, str(trace_id), job_type))
        inserted = cursor.fetchone() is not None
    return inserted
