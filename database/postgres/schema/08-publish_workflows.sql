-- database/postgres/schema/08-publish_workflows.sql
-- Publishing workflow for promoting models from team to common workspace

-- Publish workflow status enum
CREATE TYPE publish_status AS ENUM ('pending', 'approved', 'rejected', 'cancelled');

-- Publish requests
CREATE TABLE IF NOT EXISTS publish_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    source_workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    target_workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    
    -- Request details
    version INT NOT NULL,
    status publish_status NOT NULL DEFAULT 'pending',
    requested_by UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    requested_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- Request message
    message TEXT,
    
    -- Resolution
    resolved_by UUID REFERENCES users(id) ON DELETE SET NULL,
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_message TEXT,
    
    -- Published model reference (if approved)
    published_model_id UUID REFERENCES models(id) ON DELETE SET NULL,
    
    CONSTRAINT valid_workspace_transition CHECK (source_workspace_id != target_workspace_id)
);

-- Publish reviews
CREATE TABLE IF NOT EXISTS publish_reviews (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publish_request_id UUID NOT NULL REFERENCES publish_requests(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    
    -- Review details
    status VARCHAR(20) NOT NULL, -- approve, request_changes, comment
    comment TEXT,
    reviewed_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT valid_review_status CHECK (status IN ('approve', 'request_changes', 'comment'))
);

-- Publish approvals
CREATE TABLE IF NOT EXISTS publish_approvals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publish_request_id UUID NOT NULL REFERENCES publish_requests(id) ON DELETE CASCADE,
    approver_id UUID NOT NULL REFERENCES users(id) ON DELETE SET NULL,
    
    -- Approval details
    approved BOOLEAN NOT NULL,
    comment TEXT,
    approved_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_approval UNIQUE (publish_request_id, approver_id)
);

-- Publish notifications
CREATE TABLE IF NOT EXISTS publish_notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    publish_request_id UUID NOT NULL REFERENCES publish_requests(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification details
    type VARCHAR(50) NOT NULL, -- request_created, review_added, approved, rejected
    message TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    read_at TIMESTAMP WITH TIME ZONE
);

-- Indexes
CREATE INDEX idx_publish_requests_model_id ON publish_requests(model_id);
CREATE INDEX idx_publish_requests_source_workspace ON publish_requests(source_workspace_id);
CREATE INDEX idx_publish_requests_target_workspace ON publish_requests(target_workspace_id);
CREATE INDEX idx_publish_requests_status ON publish_requests(status);
CREATE INDEX idx_publish_requests_requested_by ON publish_requests(requested_by);
CREATE INDEX idx_publish_requests_requested_at ON publish_requests(requested_at);

CREATE INDEX idx_publish_reviews_request_id ON publish_reviews(publish_request_id);
CREATE INDEX idx_publish_reviews_reviewer_id ON publish_reviews(reviewer_id);
CREATE INDEX idx_publish_reviews_reviewed_at ON publish_reviews(reviewed_at);

CREATE INDEX idx_publish_approvals_request_id ON publish_approvals(publish_request_id);
CREATE INDEX idx_publish_approvals_approver_id ON publish_approvals(approver_id);

CREATE INDEX idx_publish_notifications_user_id ON publish_notifications(user_id);
CREATE INDEX idx_publish_notifications_is_read ON publish_notifications(is_read);
CREATE INDEX idx_publish_notifications_created_at ON publish_notifications(created_at);

-- Function to create notifications when publish request is created
CREATE OR REPLACE FUNCTION create_publish_notifications()
RETURNS TRIGGER AS $$
BEGIN
    -- Notify all admins in target workspace
    INSERT INTO publish_notifications (publish_request_id, user_id, type, message)
    SELECT 
        NEW.id,
        wm.user_id,
        'request_created',
        'New publish request for model: ' || m.name
    FROM workspace_members wm
    JOIN models m ON m.id = NEW.model_id
    WHERE wm.workspace_id = NEW.target_workspace_id
    AND wm.role = 'admin';
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER notify_publish_request
    AFTER INSERT ON publish_requests
    FOR EACH ROW
    EXECUTE FUNCTION create_publish_notifications();

-- Function to update model status when published
CREATE OR REPLACE FUNCTION update_model_on_publish()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'approved' AND OLD.status != 'approved' THEN
        UPDATE models
        SET status = 'published',
            published_at = NEW.resolved_at,
            published_by = NEW.resolved_by
        WHERE id = NEW.model_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_model_status_on_publish
    AFTER UPDATE OF status ON publish_requests
    FOR EACH ROW
    WHEN (NEW.status = 'approved')
    EXECUTE FUNCTION update_model_on_publish();

-- View for publish request details
CREATE OR REPLACE VIEW publish_requests_detailed AS
SELECT 
    pr.id,
    pr.model_id,
    m.name as model_name,
    pr.source_workspace_id,
    ws.name as source_workspace_name,
    pr.target_workspace_id,
    wt.name as target_workspace_name,
    pr.version,
    pr.status,
    pr.message,
    pr.requested_at,
    pr.resolved_at,
    u_req.full_name as requested_by_name,
    u_req.email as requested_by_email,
    u_res.full_name as resolved_by_name,
    (
        SELECT COUNT(*)
        FROM publish_reviews
        WHERE publish_request_id = pr.id
    ) as review_count,
    (
        SELECT COUNT(*)
        FROM publish_approvals
        WHERE publish_request_id = pr.id
        AND approved = true
    ) as approval_count
FROM publish_requests pr
LEFT JOIN models m ON pr.model_id = m.id
LEFT JOIN workspaces ws ON pr.source_workspace_id = ws.id
LEFT JOIN workspaces wt ON pr.target_workspace_id = wt.id
LEFT JOIN users u_req ON pr.requested_by = u_req.id
LEFT JOIN users u_res ON pr.resolved_by = u_res.id;

-- Comments
COMMENT ON TABLE publish_requests IS 'Requests to publish models from team to common workspace';
COMMENT ON TABLE publish_reviews IS 'Review comments on publish requests';
COMMENT ON TABLE publish_approvals IS 'Formal approvals required for publishing';
COMMENT ON TABLE publish_notifications IS 'Notifications for publish workflow events';