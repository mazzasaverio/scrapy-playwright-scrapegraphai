
-- name: insert_frontier_url<!
INSERT INTO frontier_url (url, category, type, depth, is_target)
VALUES (:url, :category, :type_, :depth, :is_target)
ON CONFLICT (url, category) DO NOTHING
RETURNING id;

-- name: get_unprocessed_urls
SELECT id, url, category, type, depth, is_target 
FROM frontier_url 
WHERE processed_at IS NULL 
ORDER BY created_at ASC 
LIMIT :limit;

-- name: mark_url_processed!
UPDATE frontier_url 
SET processed_at = CURRENT_TIMESTAMP,
    failed_attempts = CASE WHEN :success THEN failed_attempts 
                         ELSE failed_attempts + 1 END,
    last_error = CASE WHEN :success THEN NULL ELSE :error_message END
WHERE id = :url_id;

-- name: update_config_url_log!
INSERT INTO config_url_log (
    url, category, type, last_checked_at, 
    success_count, failure_count, last_status
)
VALUES (
    :url, :category, :type_, CURRENT_TIMESTAMP, 
    CASE WHEN :success THEN 1 ELSE 0 END,
    CASE WHEN :success THEN 0 ELSE 1 END,
    :status
)
ON CONFLICT (url, category) 
DO UPDATE SET
    last_checked_at = CURRENT_TIMESTAMP,
    success_count = CASE WHEN :success 
                       THEN config_url_log.success_count + 1 
                       ELSE config_url_log.success_count END,
    failure_count = CASE WHEN :success 
                       THEN config_url_log.failure_count 
                       ELSE config_url_log.failure_count + 1 END,
    last_status = :status;
