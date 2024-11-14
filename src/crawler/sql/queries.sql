-- name: insert_frontier_url^
INSERT INTO frontier_url (
        url,
        category,
        url_type,
        depth,
        max_depth,
        main_domain,
        target_patterns,
        seed_pattern,
        is_target,
        parent_url,
        url_state
    )
VALUES (
        :url,
        :category,
        :url_type,
        :depth,
        :max_depth,
        :main_domain,
        :target_patterns,
        :seed_pattern,
        :is_target,
        :parent_url,
        :url_state
    ) ON CONFLICT (url, category) DO NOTHING
RETURNING id;
-- name: get_unprocessed_urls
SELECT *
FROM frontier_url
WHERE url_state = 'pending'
ORDER BY insert_date ASC
LIMIT :limit;
-- name: mark_url_processed!
UPDATE frontier_url
SET url_state = CASE
        WHEN :success THEN 'processed'
        ELSE 'failed'
    END,
    last_update = CURRENT_TIMESTAMP,
    error_message = CASE
        WHEN :success THEN NULL
        ELSE :error_message
    END
WHERE id = :url_id;
-- name: insert_config_log^
INSERT INTO config_url_log (
        url,
        category,
        url_type,
        config_state,
        max_depth,
        target_patterns,
        seed_pattern,
        start_time
    )
VALUES (
        :url,
        :category,
        :url_type,
        :config_state,
        :max_depth,
        :target_patterns,
        :seed_pattern,
        :start_time
    ) ON CONFLICT (url, category) DO
UPDATE
SET config_state = EXCLUDED.config_state,
    max_depth = EXCLUDED.max_depth,
    target_patterns = EXCLUDED.target_patterns,
    seed_pattern = EXCLUDED.seed_pattern,
    start_time = EXCLUDED.start_time,
    updated_at = CURRENT_TIMESTAMP
RETURNING id;
-- Update update_config_state query
-- name: update_config_state!
UPDATE config_url_log
SET config_state = :config_state,
    error_message = :error_message,
    target_urls_found = target_urls_found + :target_count,
    seed_urls_found = seed_urls_found + :seed_count,
    end_time = CURRENT_TIMESTAMP,
    processing_duration = EXTRACT(
        EPOCH
        FROM CURRENT_TIMESTAMP - start_time
    )
WHERE id = :log_id;