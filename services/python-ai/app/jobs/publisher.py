from __future__ import annotations

from uuid import UUID, uuid4


def publish_job(conn, news_event_id: int, trace_id: UUID, job_type: str = "llm_analysis_company") -> bool:
    job_uuid = uuid4()
    sql = (
        "INSERT INTO analysis_jobs (job_uuid, news_event_id, trace_id, job_type, status) "
        "VALUES (%s, %s, %s, %s, 'pending') "
        "ON CONFLICT (news_event_id, job_type) DO NOTHING "
        "RETURNING 1"
    )
    with conn.cursor() as cursor:
        cursor.execute(sql, (str(job_uuid), news_event_id, str(trace_id), job_type))
        inserted = cursor.fetchone() is not None
    conn.commit()
    return inserted
