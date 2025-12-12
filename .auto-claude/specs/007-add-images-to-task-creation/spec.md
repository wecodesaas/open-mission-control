# Specification: Add Images to Task Creation

## Overview

Enable users to attach reference images (screenshots, mockups, diagrams) when creating tasks in the Auto Build UI. This feature allows users to provide visual context to the AI agents by including screenshots of bugs, UI mockups, architecture diagrams, or any visual reference material that helps clarify the task requirements. The images will be stored in the task's spec directory and referenced in the requirements.json for downstream consumption by the spec creation pipeline.

## Workflow Type

**Type**: feature

**Rationale**: This is a new capability that adds image attachment support across the task creation flow. It involves frontend UI components, IPC communication, file handling in the main process, and integration with the existing spec directory structure.

## Task Scope

### Services Involved
- **auto-claude-ui/renderer** (primary) - TaskCreationWizard component, store updates
- **auto-claude-ui/main** (integration) - IPC handlers for file operations
- **auto-claude-ui/preload** (integration) - API bridge updates
- **auto-claude-ui/shared** (integration) - Type definitions

### This Task Will:
- [ ] Add image upload UI to TaskCreationWizard with drag-and-drop support
- [ ] Create ImageUpload component with preview and removal capabilities
- [ ] Extend TaskMetadata type to include image references
- [ ] Update TASK_CREATE IPC handler to process and store images
- [ ] Save images to spec directory as attachments/
- [ ] Update requirements.json schema to include attached_images array
- [ ] Add image file validation (type, size limits)

### Out of Scope:
- Image editing or cropping within the UI
- Cloud storage integration (images are stored locally in spec directory)
- Image compression or optimization
- OCR or automatic image analysis
- Inline image display in spec.md (images are referenced, not embedded)

## Service Context

### auto-claude-ui (Electron App)

**Tech Stack:**
- Language: TypeScript
- Framework: Electron + React
- UI Components: shadcn/ui with Tailwind CSS
- State Management: Zustand stores
- Build Tool: Electron Vite

**Entry Point:** `auto-claude-ui/src/main/index.ts` (main process), `auto-claude-ui/src/renderer/main.tsx` (renderer)

**How to Run:**
```bash
cd auto-claude-ui
npm run dev
```

**Port:** N/A (desktop application)

## Files to Modify

| File | Service | What to Change |
|------|---------|---------------|
| `auto-claude-ui/src/renderer/components/TaskCreationWizard.tsx` | renderer | Add ImageUpload component, handle image state |
| `auto-claude-ui/src/shared/types.ts` | shared | Extend TaskMetadata with attachedImages field |
| `auto-claude-ui/src/shared/constants.ts` | shared | Add image-related constants (max size, allowed types) |
| `auto-claude-ui/src/main/ipc-handlers.ts` | main | Update TASK_CREATE to handle image data |
| `auto-claude-ui/src/preload/index.ts` | preload | Update createTask API signature |

## Files to Create

| File | Service | Purpose |
|------|---------|---------|
| `auto-claude-ui/src/renderer/components/ImageUpload.tsx` | renderer | Reusable image upload component with drag-drop |

## Files to Reference

These files show patterns to follow:

| File | Pattern to Copy |
|------|----------------|
| `auto-claude-ui/src/renderer/components/ui/input.tsx` | Input component styling with file input support |
| `auto-claude-ui/src/renderer/components/TaskCreationWizard.tsx` | Form state management and submission patterns |
| `auto-claude-ui/src/main/ipc-handlers.ts` | IPC handler patterns for file operations |
| `auto-claude-ui/src/shared/types.ts` | Type definition patterns for interfaces |

## Patterns to Follow

### UI Component Pattern (from existing components)

From `auto-claude-ui/src/renderer/components/ui/input.tsx`:

```typescript
const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          'flex h-10 w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground',
          // ... styling classes
          'file:border-0 file:bg-transparent file:text-sm file:font-medium',
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
```

**Key Points:**
- Use forwardRef pattern for form inputs
- Apply cn() utility for class composition
- Include file input styling variants

### IPC Handler Pattern (from existing handlers)

From `auto-claude-ui/src/main/ipc-handlers.ts`:

```typescript
ipcMain.handle(
  IPC_CHANNELS.TASK_CREATE,
  async (
    _,
    projectId: string,
    title: string,
    description: string,
    metadata?: TaskMetadata
  ): Promise<IPCResult<Task>> => {
    // ... validation and processing
    const specDir = path.join(specsDir, specId);
    mkdirSync(specDir, { recursive: true });
    // ... file operations
    return { success: true, data: task };
  }
);
```

**Key Points:**
- Use Promise-based handlers with IPCResult return type
- Create directories with recursive option
- Handle errors gracefully with error messages

### State Management Pattern (from TaskCreationWizard)

```typescript
const [formData, setFormData] = useState({
  title: '',
  description: '',
  // Add: images: [] as ImageAttachment[]
});

const handleSubmit = async () => {
  // Validation
  // API call
  // Reset state
};
```

## Requirements

### Functional Requirements

1. **Image Selection**
   - Description: Users can select images via file picker or drag-and-drop
   - Acceptance: Click "Add Images" opens file dialog filtered to image types; drag-drop zone accepts image files

2. **Image Preview**
   - Description: Selected images show thumbnails with filename and size
   - Acceptance: Each image displays as thumbnail with name, size, and remove button

3. **Image Removal**
   - Description: Users can remove images before task submission
   - Acceptance: Clicking X on image thumbnail removes it from the upload list

4. **Image Storage**
   - Description: Images are saved to spec directory when task is created
   - Acceptance: Images saved to `{spec-dir}/attachments/` with preserved filenames

5. **Requirements Integration**
   - Description: Image references are added to requirements.json
   - Acceptance: requirements.json contains `attached_images` array with relative paths

6. **File Validation**
   - Description: Only valid image types and sizes are accepted
   - Acceptance: Rejects non-image files; warns on files over 10MB; limits to 10 images

### Non-Functional Requirements

1. **Performance**
   - Image previews should generate within 200ms
   - Total upload payload should not block UI

2. **UX Consistency**
   - Match existing form styling from TaskCreationWizard
   - Use consistent spacing and typography

### Edge Cases

1. **Large Images** - Display warning for images over 10MB, allow upload but recommend compression
2. **Invalid File Types** - Show toast error, reject file, list allowed types
3. **Duplicate Names** - Append timestamp suffix to prevent overwrites
4. **Maximum Images** - Disable upload when 10 images reached, show count
5. **Failed Storage** - Roll back partial uploads, show error message

## Implementation Notes

### DO
- Use the existing `cn()` utility for class composition
- Follow the existing IPC pattern with IPCResult return types
- Store images as base64 in IPC transport, decode to files in main process
- Use relative paths in requirements.json for portability
- Add constants for MAX_IMAGE_SIZE (10MB) and ALLOWED_IMAGE_TYPES

### DON'T
- Don't use external image hosting or cloud storage
- Don't modify the core TaskMetadata type unnecessarily - use a separate images field
- Don't block the main thread with synchronous file operations
- Don't embed images directly in spec.md (use references instead)

## Development Environment

### Start Services

```bash
cd auto-claude-ui
npm run dev
```

### Required Environment Variables
- None specific to this feature

## Technical Design

### ImageAttachment Type

```typescript
interface ImageAttachment {
  id: string;           // Unique identifier (UUID)
  filename: string;     // Original filename
  mimeType: string;     // e.g., 'image/png'
  size: number;         // Size in bytes
  data?: string;        // Base64 data (for transport)
  path?: string;        // Relative path after storage
  thumbnail?: string;   // Base64 thumbnail for preview
}
```

### Updated Task Creation Flow

1. User selects images in TaskCreationWizard
2. Images converted to base64 with metadata
3. createTask IPC call includes images array
4. Main process:
   - Creates `{spec-dir}/attachments/` directory
   - Decodes and saves each image
   - Updates requirements.json with image references
5. Returns task with image paths

### Requirements.json Schema Addition

```json
{
  "task_description": "...",
  "workflow_type": "feature",
  "attached_images": [
    {
      "filename": "screenshot.png",
      "path": "attachments/screenshot.png",
      "description": "Bug screenshot showing the error state"
    }
  ]
}
```

## Success Criteria

The task is complete when:

1. [ ] Users can drag-and-drop or select images in task creation form
2. [ ] Image thumbnails display with remove option
3. [ ] Images are saved to spec directory on task creation
4. [ ] requirements.json includes attached_images array
5. [ ] File type and size validation works correctly
6. [ ] No console errors during image upload flow
7. [ ] Existing tests still pass
8. [ ] UI matches existing design patterns

## QA Acceptance Criteria

**CRITICAL**: These criteria must be verified by the QA Agent before sign-off.

### Unit Tests
| Test | File | What to Verify |
|------|------|----------------|
| ImageUpload renders | `auto-claude-ui/src/renderer/components/__tests__/ImageUpload.test.tsx` | Component renders with drag-drop zone |
| File validation | `auto-claude-ui/src/renderer/components/__tests__/ImageUpload.test.tsx` | Rejects invalid types, large files |
| Image removal | `auto-claude-ui/src/renderer/components/__tests__/ImageUpload.test.tsx` | Remove button removes image from list |

### Integration Tests
| Test | Services | What to Verify |
|------|----------|----------------|
| Task creation with images | renderer ↔ main | Images transferred via IPC and saved correctly |
| Requirements.json update | main | attached_images field populated correctly |

### End-to-End Tests
| Flow | Steps | Expected Outcome |
|------|-------|------------------|
| Add images to task | 1. Create new task 2. Drag image to upload area 3. Submit task | Task created with image in attachments/ |
| Remove image before submit | 1. Add image 2. Click remove 3. Submit | Task created without images |
| Max images limit | 1. Try to add 11 images | Only 10 accepted, warning shown |

### Browser Verification (Electron)
| Page/Component | URL | Checks |
|----------------|-----|--------|
| TaskCreationWizard | Task creation modal | Drag-drop zone visible, file picker works |
| Image preview | Task creation modal | Thumbnails render correctly |

### Database Verification (Filesystem)
| Check | Query/Command | Expected |
|-------|---------------|----------|
| Images saved | `ls {spec-dir}/attachments/` | Image files present |
| Requirements updated | `cat {spec-dir}/requirements.json` | attached_images array exists |

### QA Sign-off Requirements
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] All E2E tests pass
- [ ] Manual testing complete
- [ ] No regressions in existing functionality
- [ ] Code follows established patterns
- [ ] No security vulnerabilities introduced
- [ ] Image data not persisted unnecessarily in memory
