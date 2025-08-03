"""
Schemachange templater for SQLFluff.

This templater integrates with the schemachange database change management tool,
using schemachange's native render functionality to process Jinja templates.
"""

import subprocess
import tempfile
import os
import json
import logging
from typing import Dict, Any

from sqlfluff.core.templaters.base import TemplatedFile, RawTemplater
from sqlfluff.core.errors import SQLTemplaterError

# Try to import the slice classes
try:
    from sqlfluff.core.templaters.base import RawFileSlice, TemplatedFileSlice
except ImportError:
    try:
        from sqlfluff.core.templaters import RawFileSlice, TemplatedFileSlice
    except ImportError:
        # If we can't import them, we'll need to create our own
        from dataclasses import dataclass
        from typing import Optional
        
        @dataclass
        class RawFileSlice:
            raw: str
            slice_type: str
            source_idx: int
            block_idx: int
            tag: Optional[str] = None
        
        @dataclass
        class TemplatedFileSlice:
            slice_type: str
            source_slice: slice
            templated_slice: slice

logger = logging.getLogger(__name__)


class SchemachangeTemplater(RawTemplater):
    """
    A templater that uses schemachange's native render command to process Jinja templates.
    
    This templater calls schemachange render directly, ensuring 100% compatibility
    with schemachange's templating system including:
    - Jinja2 templating with variables from schemachange-config.yml
    - Macro templates from modules folder
    - Environment variable substitution
    - All schemachange templating features
    """
    
    name = "schemachange"
    sequential_fail_limit = 3
    # print("SchemachangeTemplater initialized")
        
    def config_pairs(self):
        """Return configuration options for this templater."""
        return [
            ("config_folder", '.'),
            ("root_folder", '.'),
            ("modules_folder", '.'),
            ("vars", {}),
            ("verbose", False),
        ]

    def process(self, *, fname, in_str, config=None, formatter=None):
        """
        Process the given string using schemachange's native render command.
        
        Args:
            fname: The filename being processed
            in_str: The input SQL string
            config: SQLFluff configuration object
            formatter: Optional formatter (not used)
            
        Returns:
            TemplatedFile: The templated result
        """
        # print(f"🔧 PROCESS called - Processing file: {fname}")
        # print(f"📝 Input string: {in_str}")
        # print(f"🎨 Formatter: {formatter}")
        
        # Get templater configuration
        try:
            templater_section = config.get_section(("templater", "SchemachangeTemplater"))
            # print(f"Templater config section: {templater_section}")
        except Exception as e:
            logger.warning(f"Error getting templater section: {e}")
            templater_section = {}
        try:
            # Get templater configuration - using correct path
            templater_config = config.get_section(("templater", "SchemachangeTemplater")) or {}
            ends_with_semicolon = in_str.endswith(';')
            ends_with_semicolon_newline = in_str.endswith(';\n')
            # Create temporary file for SQL content
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sql', delete=False, dir=os.getcwd()) as  temp_file:
                temp_file.write(in_str)
                temp_file_path = temp_file.name
            
            try:
                # Build schemachange render command
                cmd = ['schemachange', 'render',  os.path.basename(temp_file_path)]
                # Add optional parameters based on configuration
                if templater_config.get('config_folder'):
                    cmd.extend(['--config-folder', templater_config['config_folder']])
                    
                if templater_config.get('root_folder'):
                    cmd.extend(['-f', templater_config['root_folder']])
                    
                if templater_config.get('modules_folder'):
                    cmd.extend(['-m', templater_config['modules_folder']])
                    
                if templater_config.get('vars'):
                    # Convert vars to JSON string for schemachange
                    vars_json = json.dumps(templater_config['vars'])
                    cmd.extend(['--vars', vars_json])
                    
                if templater_config.get('verbose', False):
                    cmd.append('-v')
                
                logger.debug(f"Executing schemachange command: {' '.join(cmd)}")
                # print(f"Executing schemachange command: {' '.join(cmd)}")
                
                # Execute schemachange render
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    cwd=os.getcwd()
                )
                
                if result.returncode != 0:
                    error_msg = result.stderr.strip() or result.stdout.strip()
                    raise SQLTemplaterError(
                        f"Schemachange render failed: {error_msg}",
                        line_no=None,
                        line_pos=None,
                    )
                
                # Parse rendered content from schemachange stdout 
                stdout = result.stdout.strip()
                if 'content=' in stdout:
                    # print(f"📝 Found 'content=' in stdout, attempting regex extraction")
                    # Extract content from the success log line - more robust regex
                    import re
                    # Try first pattern that captures everything between content= and schemachange_version=
                    match = re.search(r'content=(.+?)(?=\s*schemachange_version=)', stdout, re.DOTALL)
                    if not match:
                        # Fallback: try to capture content= to end of line/output
                        match = re.search(r'content=(.+?)(?=\s*$)', stdout, re.DOTALL | re.MULTILINE)
                    
                    if match:
                        rendered_sql = match.group(1)
                        # fix for when schemachange deletes the trailing semicolon and whitespace if present on render
                        if ends_with_semicolon:
                            rendered_sql = rendered_sql + ';'
                        if ends_with_semicolon_newline:
                            rendered_sql = rendered_sql + ';\n'
                        # print(f"✅ Regex extraction SUCCESS")
                    else:
                        logger.warning("Regex extraction failed - using original SQL")
                        rendered_sql = in_str  # Fallback to original
                else:
                    logger.warning("No 'content=' found in stdout - using original SQL")
                    rendered_sql = in_str  # Fallback to original
                
                # Handle case where schemachange returns empty output
                if not rendered_sql:
                    logger.warning("Schemachange render returned empty output, using original SQL")
                    rendered_sql = in_str
                
                # Preserve trailing whitespace from original input to avoid issues with fix operations
                # Check if original input ends with whitespace/newlines
                original_trailing = ''
                if in_str and in_str[-1] in (' ', '\t', '\n', '\r'):
                    # Find all trailing whitespace
                    i = len(in_str) - 1
                    while i >= 0 and in_str[i] in (' ', '\t', '\n', '\r'):
                        i -= 1
                    original_trailing = in_str[i + 1:]
                    
                    # If rendered SQL doesn't end with the same trailing whitespace, add it
                    if original_trailing and not rendered_sql.endswith(original_trailing):
                        rendered_sql = rendered_sql.rstrip() + original_trailing
                
                # print(f"✅ Rendered SQL content:\n{rendered_sql}")
                # print(f"📏 Length: {len(rendered_sql)} characters")
                
                logger.debug(f"Schemachange render successful. Input length: {len(in_str)}, Output length: {len(rendered_sql)}")
                
                # Manual slicing approach - create position mapping between input and output
                # print(f"🔍 Creating manual slices:")
                # print(f"   Input: {repr(in_str)} (length: {len(in_str)})")
                # print(f"   Output: {repr(rendered_sql)} (length: {len(rendered_sql)})")
                
                # Create accurate slices with contiguity validation
                import re
                from difflib import SequenceMatcher
                
                templated_file_slices = []
                raw_file_slices = []
                
                # Use difflib to find the actual differences between input and rendered SQL
                matcher = SequenceMatcher(None, in_str, rendered_sql)
                
                # Process each matching block and difference, ensuring contiguity
                last_source_end = 0
                last_templated_end = 0
                
                for tag, i1, i2, j1, j2 in matcher.get_opcodes():
                    # Fill any gap in source coverage
                    if i1 > last_source_end:
                        gap_content = in_str[last_source_end:i1]
                        # This gap represents removed Jinja control structures
                        templated_file_slices.append(
                            TemplatedFileSlice(
                                slice_type='templated',
                                source_slice=slice(last_source_end, i1),
                                templated_slice=slice(last_templated_end, last_templated_end)  # Zero-length in output
                            )
                        )
                        raw_file_slices.append(
                            RawFileSlice(
                                raw=gap_content,
                                slice_type='templated',
                                source_idx=last_source_end,
                                block_idx=0,
                                tag=None
                            )
                        )
                    
                    # Process the current operation
                    if tag == 'equal':
                        # Literal content that didn't change
                        if i2 > i1:  # Only if there's actual content
                            literal_content = in_str[i1:i2]
                            
                            templated_file_slices.append(
                                TemplatedFileSlice(
                                    slice_type='literal',
                                    source_slice=slice(i1, i2),
                                    templated_slice=slice(j1, j2)
                                )
                            )
                            
                            raw_file_slices.append(
                                RawFileSlice(
                                    raw=literal_content,
                                    slice_type='literal',
                                    source_idx=i1,
                                    block_idx=0,
                                    tag=None
                                )
                            )
                    
                    elif tag in ['replace', 'delete', 'insert']:
                        # This represents a template substitution or change
                        if i2 > i1:  # There was content in the source
                            source_content = in_str[i1:i2]
                            
                            # Check if this is a Jinja template variable or control structure
                            if ('{{' in source_content and '}}' in source_content) or ('{%' in source_content and '%}' in source_content):
                                slice_type = 'templated'
                            else:
                                slice_type = 'literal'
                            
                            templated_file_slices.append(
                                TemplatedFileSlice(
                                    slice_type=slice_type,
                                    source_slice=slice(i1, i2),
                                    templated_slice=slice(j1, j2)
                                )
                            )
                            
                            raw_file_slices.append(
                                RawFileSlice(
                                    raw=source_content,
                                    slice_type=slice_type,
                                    source_idx=i1,
                                    block_idx=0,
                                    tag=None
                                )
                            )
                    
                    # Update tracking positions
                    last_source_end = max(last_source_end, i2)
                    last_templated_end = max(last_templated_end, j2)
                
                # Handle any remaining content at the end
                if last_source_end < len(in_str):
                    gap_content = in_str[last_source_end:]
                    templated_file_slices.append(
                        TemplatedFileSlice(
                            slice_type='templated',
                            source_slice=slice(last_source_end, len(in_str)),
                            templated_slice=slice(last_templated_end, last_templated_end)  # Zero-length in output
                        )
                    )
                    raw_file_slices.append(
                        RawFileSlice(
                            raw=gap_content,
                            slice_type='templated',
                            source_idx=last_source_end,
                            block_idx=0,
                            tag=None
                        )
                    )
                
                # Validate contiguity
                def validate_slice_contiguity(slices, total_length, slice_name):
                    if not slices:
                        return True, []
                    
                    errors = []
                    expected_pos = 0
                    
                    for i, slice_obj in enumerate(slices):
                        if hasattr(slice_obj, 'source_slice'):
                            start = slice_obj.source_slice.start
                            end = slice_obj.source_slice.stop
                        else:
                            start = slice_obj.source_idx
                            end = start + len(slice_obj.raw)
                        
                        if start != expected_pos:
                            errors.append(f"Gap in {slice_name} at position {expected_pos}-{start}")
                        
                        expected_pos = end
                    
                    if expected_pos != total_length:
                        errors.append(f"Final {slice_name} position {expected_pos} != total length {total_length}")
                    
                    return len(errors) == 0, errors
                
                # Validate both slice sets
                source_valid, source_errors = validate_slice_contiguity(templated_file_slices, len(in_str), "source slices")
                
                # Validate template slice coverage 
                total_templated_length = sum(
                    max(0, slice_obj.templated_slice.stop - slice_obj.templated_slice.start)
                    for slice_obj in templated_file_slices
                )
                template_length_valid = total_templated_length == len(rendered_sql)
                
                # If validation fails, fall back to simple slicing
                if not source_valid or not template_length_valid:
                    logger.warning(f"Complex slicing failed, falling back to simple approach")
                    logger.warning(f"Source valid: {source_valid}, Template length: {total_templated_length}/{len(rendered_sql)}")
                    
                    # Simple fallback: treat entire input as templated
                    templated_file_slices = [
                        TemplatedFileSlice(
                            slice_type='templated',
                            source_slice=slice(0, len(in_str)),
                            templated_slice=slice(0, len(rendered_sql))
                        )
                    ]
                    
                    raw_file_slices = [
                        RawFileSlice(
                            raw=in_str,
                            slice_type='templated',
                            source_idx=0,
                            block_idx=0,
                            tag=None
                        )
                    ]
                    
                    logger.info("Using simple fallback slicing for complex template")
                else:
                    logger.debug("Complex slicing validation passed")
                
                # print(f"   Created {len(templated_file_slices)} slices")
                # print(f"   templated_file_slices: {templated_file_slices}")
                # print(f"   raw_file_slices: {raw_file_slices}")
                
                # Create the templated file object with manual slicing
                templated_file = TemplatedFile(
                source_str=in_str,
                templated_str=rendered_sql,
                fname=fname,
                    sliced_file=templated_file_slices,
                    raw_sliced=raw_file_slices,
                )
                
                return templated_file, []
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except OSError:
                    logger.warning(f"Failed to clean up temporary file: {temp_file_path}")
                
        except subprocess.TimeoutExpired:
            raise SQLTemplaterError(
                "Schemachange render command timed out (30s limit)",
                line_no=None,
                line_pos=None,
            )
        except FileNotFoundError:
            raise SQLTemplaterError(
                "Schemachange command not found. Please ensure schemachange is installed and available in PATH.",
                line_no=None,
                line_pos=None,
            )
        except Exception as e:
            raise SQLTemplaterError(
                f"Error calling schemachange render: {str(e)}",
                line_no=None,
                line_pos=None,
            )