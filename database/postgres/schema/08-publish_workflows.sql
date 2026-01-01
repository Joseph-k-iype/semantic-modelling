-- database/postgres/schema/08-publish_workflows.sql
-- Publishing workflow tables for model governance

-- Drop existing tables if exist (for clean reinstall)
DROP TABLE IF EXISTS publish_reviews CASCADE;
DROP TABLE IF EXISTS publish_approvals CASCADE;
DROP TABLE IF EXISTS publish_requests CASCADE;

-- Publish requests table
CREATE TABLE publish_requests (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    model_id UUID NOT NULL REFERENCES models(id) ON DELETE CASCADE,
    version_id UUID REFERENCES versions(id) ON DELETE SET NULL,
    source_workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    target_workspace_id UUID NOT NULL REFERENCES workspaces(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    justification TEXT,
    status publish_status DEFAULT 'DRAFT' NOT NULL,
    priority VARCHAR(20) DEFAULT 'MEDIUM',
    due_date TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'::JSONB,
    submitted_at TIMESTAMP WITH TIME ZONE,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    published_at TIMESTAMP WITH TIME ZONE,
    rejection_reason TEXT,
    created_by UUID NOT NULL REFERENCES users(id) ON DELETE RESTRICT,
    updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT publish_requests_title_check CHECK (LENGTH(TRIM(title)) >= 1),
    CONSTRAINT publish_requests_priority_check CHECK (priority IN ('LOW', 'MEDIUM', 'HIGH', 'URGENT')),
    CONSTRAINT publish_requests_source_target_check CHECK (source_workspace_id != target_workspace_id),
    CONSTRAINT publish_requests_status_dates_check CHECK (
        (status = 'DRAFT' AND submitted_at IS NULL) OR
        (status != 'DRAFT' AND submitted_at IS NOT NULL)
    )
);

-- Publish approvals table
CREATE TABLE publish_approvals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publish_request_id UUID NOT NULL REFERENCES publish_requests(id) ON DELETE CASCADE,
    approver_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    comments TEXT,
    approved_at TIMESTAMP WITH TIME ZONE,
    rejected_at TIMESTAMP WITH TIME ZONE,
    is_required BOOLEAN DEFAULT TRUE NOT NULL,
    approval_order INTEGER DEFAULT 0 NOT NULL,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT publish_approvals_status_check CHECK (status IN ('PENDING', 'APPROVED', 'REJECTED', 'SKIPPED')),
    CONSTRAINT publish_approvals_approval_order_check CHECK (approval_order >= 0),
    CONSTRAINT publish_approvals_status_dates_check CHECK (
        (status = 'PENDING' AND approved_at IS NULL AND rejected_at IS NULL) OR
        (status = 'APPROVED' AND approved_at IS NOT NULL AND rejected_at IS NULL) OR
        (status = 'REJECTED' AND approved_at IS NULL AND rejected_at IS NOT NULL)
    ),
    -- Unique constraint: one approval per approver per request
    CONSTRAINT publish_approvals_unique UNIQUE(publish_request_id, approver_id)
);

-- Publish reviews table (for review comments during the workflow)
CREATE TABLE publish_reviews (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    publish_request_id UUID NOT NULL REFERENCES publish_requests(id) ON DELETE CASCADE,
    reviewer_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    review_type VARCHAR(50) NOT NULL,
    comments TEXT NOT NULL,
    rating INTEGER,
    attachments JSONB DEFAULT '[]'::JSONB,
    metadata JSONB DEFAULT '{}'::JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    
    -- Constraints
    CONSTRAINT publish_reviews_review_type_check CHECK (review_type IN (
        'TECHNICAL',
        'BUSINESS',
        'COMPLIANCE',
        'GENERAL'
    )),
    CONSTRAINT publish_reviews_rating_check CHECK (rating IS NULL OR (rating >= 1 AND rating <= 5)),
    CONSTRAINT publish_reviews_comments_check CHECK (LENGTH(TRIM(comments)) >= 1)
);

-- Indexes for publish_requests table
CREATE INDEX idx_publish_requests_model_id ON publish_requests(model_id);
CREATE INDEX idx_publish_requests_version_id ON publish_requests(version_id);
CREATE INDEX idx_publish_requests_source_workspace_id ON publish_requests(source_workspace_id);
CREATE INDEX idx_publish_requests_target_workspace_id ON publish_requests(target_workspace_id);
CREATE INDEX idx_publish_requests_status ON publish_requests(status);
CREATE INDEX idx_publish_requests_priority ON publish_requests(priority);
CREATE INDEX idx_publish_requests_created_by ON publish_requests(created_by);
CREATE INDEX idx_publish_requests_submitted_at ON publish_requests(submitted_at DESC NULLS LAST);
CREATE INDEX idx_publish_requests_due_date ON publish_requests(due_date) WHERE due_date IS NOT NULL;
CREATE INDEX idx_publish_requests_created_at ON publish_requests(created_at DESC);

-- Full-text search index
CREATE INDEX idx_publish_requests_fulltext ON publish_requests 
    USING gin(to_tsvector('english', 
        COALESCE(title, '') || ' ' || 
        COALESCE(description, '') || ' ' ||
        COALESCE(justification, '')
    ));

-- Indexes for publish_approvals table
CREATE INDEX idx_publish_approvals_publish_request_id ON publish_approvals(publish_request_id);
CREATE INDEX idx_publish_approvals_approver_id ON publish_approvals(approver_id);
CREATE INDEX idx_publish_approvals_status ON publish_approvals(status);
CREATE INDEX idx_publish_approvals_approval_order ON publish_approvals(approval_order);
CREATE INDEX idx_publish_approvals_is_required ON publish_approvals(is_required) WHERE is_required = TRUE;

-- Indexes for publish_reviews table
CREATE INDEX idx_publish_reviews_publish_request_id ON publish_reviews(publish_request_id);
CREATE INDEX idx_publish_reviews_reviewer_id ON publish_reviews(reviewer_id);
CREATE INDEX idx_publish_reviews_review_type ON publish_reviews(review_type);
CREATE INDEX idx_publish_reviews_rating ON publish_reviews(rating) WHERE rating IS NOT NULL;
CREATE INDEX idx_publish_reviews_created_at ON publish_reviews(created_at DESC);

-- Trigger to update updated_at timestamp
CREATE TRIGGER update_publish_requests_updated_at
    BEFORE UPDATE ON publish_requests
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_publish_approvals_updated_at
    BEFORE UPDATE ON publish_approvals
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_publish_reviews_updated_at
    BEFORE UPDATE ON publish_reviews
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update publish request status based on approvals
CREATE OR REPLACE FUNCTION update_publish_request_status()
RETURNS TRIGGER AS $$
DECLARE
    v_total_required INTEGER;
    v_approved_count INTEGER;
    v_rejected_count INTEGER;
BEGIN
    -- Count required approvals
    SELECT 
        COUNT(*) FILTER (WHERE is_required = TRUE),
        COUNT(*) FILTER (WHERE is_required = TRUE AND status = 'APPROVED'),
        COUNT(*) FILTER (WHERE status = 'REJECTED')
    INTO v_total_required, v_approved_count, v_rejected_count
    FROM publish_approvals
    WHERE publish_request_id = NEW.publish_request_id;
    
    -- Update request status
    IF v_rejected_count > 0 THEN
        UPDATE publish_requests
        SET status = 'REJECTED',
            rejected_at = NOW()
        WHERE id = NEW.publish_request_id
        AND status = 'PENDING_REVIEW';
    ELSIF v_approved_count = v_total_required THEN
        UPDATE publish_requests
        SET status = 'APPROVED',
            approved_at = NOW()
        WHERE id = NEW.publish_request_id
        AND status = 'PENDING_REVIEW';
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER publish_approval_update_request_status
    AFTER UPDATE OF status ON publish_approvals
    FOR EACH ROW
    WHEN (OLD.status IS DISTINCT FROM NEW.status)
    EXECUTE FUNCTION update_publish_request_status();

-- Trigger to set submitted_at when status changes to PENDING_REVIEW
CREATE OR REPLACE FUNCTION set_publish_request_submitted_at()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'PENDING_REVIEW' AND OLD.status = 'DRAFT' THEN
        NEW.submitted_at = NOW();
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER publish_request_set_submitted_at
    BEFORE UPDATE OF status ON publish_requests
    FOR EACH ROW
    WHEN (OLD.status = 'DRAFT' AND NEW.status = 'PENDING_REVIEW')
    EXECUTE FUNCTION set_publish_request_submitted_at();

-- Function to submit publish request
CREATE OR REPLACE FUNCTION submit_publish_request(
    p_request_id UUID,
    p_approver_ids UUID[],
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_approver_id UUID;
    v_order INTEGER := 0;
BEGIN
    -- Update request status
    UPDATE publish_requests
    SET 
        status = 'PENDING_REVIEW',
        submitted_at = NOW(),
        updated_by = p_user_id
    WHERE id = p_request_id
    AND status = 'DRAFT';
    
    -- Create approval records
    FOREACH v_approver_id IN ARRAY p_approver_ids
    LOOP
        INSERT INTO publish_approvals (
            publish_request_id,
            approver_id,
            approval_order,
            is_required
        ) VALUES (
            p_request_id,
            v_approver_id,
            v_order,
            TRUE
        );
        v_order := v_order + 1;
    END LOOP;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to approve publish request
CREATE OR REPLACE FUNCTION approve_publish_request(
    p_request_id UUID,
    p_approver_id UUID,
    p_comments TEXT DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE publish_approvals
    SET 
        status = 'APPROVED',
        comments = p_comments,
        approved_at = NOW()
    WHERE publish_request_id = p_request_id
    AND approver_id = p_approver_id
    AND status = 'PENDING';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to reject publish request
CREATE OR REPLACE FUNCTION reject_publish_request(
    p_request_id UUID,
    p_approver_id UUID,
    p_comments TEXT
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE publish_approvals
    SET 
        status = 'REJECTED',
        comments = p_comments,
        rejected_at = NOW()
    WHERE publish_request_id = p_request_id
    AND approver_id = p_approver_id
    AND status = 'PENDING';
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Function to publish model
CREATE OR REPLACE FUNCTION publish_model(
    p_request_id UUID,
    p_user_id UUID
)
RETURNS BOOLEAN AS $$
DECLARE
    v_request RECORD;
    v_all_approved BOOLEAN;
BEGIN
    -- Get request details
    SELECT * INTO v_request
    FROM publish_requests
    WHERE id = p_request_id
    AND status = 'APPROVED';
    
    IF NOT FOUND THEN
        RAISE EXCEPTION 'Request not found or not approved';
    END IF;
    
    -- Check if all required approvals are obtained
    SELECT NOT EXISTS (
        SELECT 1 FROM publish_approvals
        WHERE publish_request_id = p_request_id
        AND is_required = TRUE
        AND status != 'APPROVED'
    ) INTO v_all_approved;
    
    IF NOT v_all_approved THEN
        RAISE EXCEPTION 'Not all required approvals obtained';
    END IF;
    
    -- Update model as published
    UPDATE models
    SET 
        is_published = TRUE,
        published_at = NOW(),
        workspace_id = v_request.target_workspace_id
    WHERE id = v_request.model_id;
    
    -- Update request status
    UPDATE publish_requests
    SET 
        status = 'PUBLISHED',
        published_at = NOW(),
        updated_by = p_user_id
    WHERE id = p_request_id;
    
    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- Function to get pending approvals for user
CREATE OR REPLACE FUNCTION get_pending_approvals(p_user_id UUID)
RETURNS TABLE (
    request_id UUID,
    model_name VARCHAR(255),
    request_title VARCHAR(255),
    priority VARCHAR(20),
    submitted_at TIMESTAMP WITH TIME ZONE,
    due_date TIMESTAMP WITH TIME ZONE,
    approval_order INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        pr.id,
        m.name,
        pr.title,
        pr.priority,
        pr.submitted_at,
        pr.due_date,
        pa.approval_order
    FROM publish_approvals pa
    JOIN publish_requests pr ON pr.id = pa.publish_request_id
    JOIN models m ON m.id = pr.model_id
    WHERE pa.approver_id = p_user_id
    AND pa.status = 'PENDING'
    AND pr.status = 'PENDING_REVIEW'
    ORDER BY pr.priority DESC, pr.submitted_at ASC;
END;
$$ LANGUAGE plpgsql STABLE;

-- Function to get publish request history
CREATE OR REPLACE FUNCTION get_publish_request_history(p_request_id UUID)
RETURNS TABLE (
    event_type VARCHAR(50),
    event_description TEXT,
    user_name VARCHAR(255),
    event_time TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    WITH events AS (
        SELECT 
            'REQUEST_CREATED' as event_type,
            'Request created' as event_description,
            u.full_name,
            pr.created_at
        FROM publish_requests pr
        JOIN users u ON u.id = pr.created_by
        WHERE pr.id = p_request_id
        
        UNION ALL
        
        SELECT 
            'REQUEST_SUBMITTED' as event_type,
            'Request submitted for review' as event_description,
            u.full_name,
            pr.submitted_at
        FROM publish_requests pr
        JOIN users u ON u.id = pr.created_by
        WHERE pr.id = p_request_id
        AND pr.submitted_at IS NOT NULL
        
        UNION ALL
        
        SELECT 
            CASE 
                WHEN pa.status = 'APPROVED' THEN 'APPROVAL_GRANTED'
                WHEN pa.status = 'REJECTED' THEN 'APPROVAL_REJECTED'
            END as event_type,
            CASE 
                WHEN pa.status = 'APPROVED' THEN 'Approved by ' || u.full_name
                WHEN pa.status = 'REJECTED' THEN 'Rejected by ' || u.full_name
            END as event_description,
            u.full_name,
            COALESCE(pa.approved_at, pa.rejected_at)
        FROM publish_approvals pa
        JOIN users u ON u.id = pa.approver_id
        WHERE pa.publish_request_id = p_request_id
        AND pa.status IN ('APPROVED', 'REJECTED')
        
        UNION ALL
        
        SELECT 
            'REVIEW_ADDED' as event_type,
            'Review added by ' || u.full_name as event_description,
            u.full_name,
            pv.created_at
        FROM publish_reviews pv
        JOIN users u ON u.id = pv.reviewer_id
        WHERE pv.publish_request_id = p_request_id
    )
    SELECT * FROM events
    ORDER BY event_time;
END;
$$ LANGUAGE plpgsql STABLE;

-- Logging
DO $$
BEGIN
    RAISE NOTICE 'Publish workflows schema created successfully';
END $$;