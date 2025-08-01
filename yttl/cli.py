# SPDX-License-Identifier: Apache-2.0

import os
from argparse import ArgumentParser
import shutil
import glob
import re
from bs4 import BeautifulSoup
from .yttl import process_video, process_playlist, is_playlist_url, load_config, LLM_PROVIDERS, LOCAL_WHISPER_DEFAULT, WHISPER_PROVIDERS
from tqdm import tqdm

OUT_DIR = 'out'
GROQ_API_KEY_VAR = 'GROQ_API_KEY'

class ProgressHooks(object):
    def __init__(self):
        self.top_bar = tqdm(total=5, position=0, bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} ')
        self.last_top = 0
        self.sub_bar = None
    def phase(self, idx, name, substeps=0, bytes=False):
        up_by = idx - self.last_top
        self.last_top = idx
        self.last_sub = 0
        if self.sub_bar is not None:
            self.sub_bar.close()
        self.top_bar.set_description(name)
        self.top_bar.update(up_by)
        if substeps != 0:
            extra = {}
            if bytes:
                extra = dict(unit='B', unit_divisor=1024, unit_scale=True)
            self.sub_bar = tqdm(total=substeps, position=1, **extra)
        else:
            self.sub_bar = None
    def subphase_step(self, val = None):
        if val is None:
            self.sub_bar.update()
            return
        up_by = val - self.last_sub
        self.last_sub = val
        self.sub_bar.update(up_by)
    def set_substeps(self, num):
        self.sub_bar.total = num
    def close(self):
        self.top_bar.close()
        if self.sub_bar is not None:
            self.sub_bar.close()

def search_files(search_terms, out_dir=OUT_DIR):
    """Search through processed video files in the output directory."""
    if not os.path.exists(out_dir):
        print(f"Output directory '{out_dir}' not found.")
        return
    
    html_files = glob.glob(os.path.join(out_dir, "*.html"))
    if not html_files:
        print(f"No HTML files found in '{out_dir}'.")
        return
    
    search_terms_lower = search_terms.lower()
    matches = []
    
    for html_file in html_files:
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            soup = BeautifulSoup(content, 'html.parser')
            
            # Extract title
            title_elem = soup.find('h1')
            title = title_elem.get_text().strip() if title_elem else "Unknown Title"
            
            # Extract video URL
            video_link = title_elem.find('a')['href'] if title_elem and title_elem.find('a') else ""
            
            # Search in title
            title_match = search_terms_lower in title.lower()
            
            # Search in summary sections
            summary_matches = []
            summary_sections = soup.find_all('section')
            for section in summary_sections:
                if section.find('h2') and 'transcript' in section.find('h2').get_text().lower():
                    continue  # Skip transcript section for summary search
                section_text = section.get_text()
                if search_terms_lower in section_text.lower():
                    # Extract a snippet around the match
                    text_lower = section_text.lower()
                    match_pos = text_lower.find(search_terms_lower)
                    start = max(0, match_pos - 50)
                    end = min(len(section_text), match_pos + len(search_terms) + 50)
                    snippet = section_text[start:end].strip()
                    if start > 0:
                        snippet = "..." + snippet
                    if end < len(section_text):
                        snippet = snippet + "..."
                    summary_matches.append(snippet)
            
            # Search in transcript
            transcript_matches = []
            transcript_segments = soup.find_all('p', class_='transcript-segment')
            for segment in transcript_segments:
                segment_text = segment.get_text()
                if search_terms_lower in segment_text.lower():
                    # Clean up the text and extract snippet
                    text_lines = segment_text.strip().split('\n')
                    clean_text = ' '.join(line.strip() for line in text_lines if line.strip())
                    transcript_matches.append(clean_text)
            
            # If we found matches, add to results
            if title_match or summary_matches or transcript_matches:
                matches.append({
                    'file': html_file,
                    'title': title,
                    'video_url': video_link,
                    'title_match': title_match,
                    'summary_matches': summary_matches,
                    'transcript_matches': transcript_matches
                })
                
        except Exception as e:
            print(f"Error processing {html_file}: {e}")
            continue
    
    # Display results
    if not matches:
        print(f"No matches found for '{search_terms}'")
        return
    
    print(f"Found {len(matches)} file(s) matching '{search_terms}':\n")
    
    for i, match in enumerate(matches, 1):
        print(f"{i}. {match['title']}")
        print(f"   File: {os.path.basename(match['file'])}")
        if match['video_url']:
            print(f"   URL: {match['video_url']}")
        
        if match['title_match']:
            print("   ✓ Found in title")
        
        if match['summary_matches']:
            print(f"   ✓ Found in summary ({len(match['summary_matches'])} match(es))")
            for snippet in match['summary_matches'][:2]:  # Show first 2 snippets
                print(f"     \"{snippet}\"")
        
        if match['transcript_matches']:
            print(f"   ✓ Found in transcript ({len(match['transcript_matches'])} match(es))")
            for snippet in match['transcript_matches'][:2]:  # Show first 2 snippets
                print(f"     \"{snippet}\"")
        
        print()

def main():
    config = load_config()
    parser = ArgumentParser(prog='yttl')
    parser.add_argument('video_url', nargs='?', help='YouTube video URL or playlist URL')
    parser.add_argument('-s', '--search', help='Search through processed videos in the output directory')
    parser.add_argument('-lp', '--llm-provider', choices = LLM_PROVIDERS.keys(), default = config.get('llm_provider'))
    parser.add_argument('-wp', '--whisper-provider', choices = WHISPER_PROVIDERS.keys(), default = config.get('whisper_provider'))
    parser.add_argument('-sb', '--sponsorblock',
                        choices = ['sponsor', 'selfpromo', 'interaction', 'intro', 'outro', 'preview', 'music', 'offtopic', 'filler'],
                        action = 'append', default = config.get('sponsorblock'))
    parser.add_argument('-lmr', '--local-model-repo', default = config.get('local_model_repo'))
    parser.add_argument('-lmf', '--local-model-file', default = config.get('local_model_file'))
    parser.add_argument('-hm', '--huggingchat-model', default = config.get('huggingchat_model'))
    parser.add_argument('-om', '-gm', '--openai-model', '--groq-model', default = config.get('openai_model'))
    parser.add_argument('-ou', '--openai-base-url', default = config.get('openai_base_url'))
    parser.add_argument('-lwm', '-wm', '--local-whisper-model', '--whisper-model',
                        choices = ['tiny', 'tiny.en', 'base', LOCAL_WHISPER_DEFAULT, 'small', 'small.en', 'medium', 'medium.en', 'large-v1', 'large-v2', 'large-v3'],
                        default = config.get('whisper_model'))
    parser.add_argument('-v', '--verbose', default = config.get('verbose'), action  = 'store_true')
    parser.add_argument('--force-local-transcribe', action = 'store_true')
    parser.add_argument('--disable-performance-optimizations', action = 'store_true', 
                       help='Disable parallel processing and other performance optimizations')
    parser.add_argument('--max-concurrent-llm', type=int, default=config.get('max_concurrent_llm', 5),
                       help='Maximum concurrent LLM requests for parallel processing')
    parser.add_argument('--performance-report', action='store_true', default=config.get('performance_report', False),
                       help='Show detailed performance statistics after processing')
    args = parser.parse_args()
    
    # Handle search functionality
    if args.search:
        search_files(args.search)
        return
    
    # Require video_url if not searching
    if not args.video_url:
        parser.error("video_url is required when not using --search")
    
    api_key = config.get(GROQ_API_KEY_VAR, None)
    api_key = config.get('openai_api_key', api_key)
    api_key = os.environ.get(GROQ_API_KEY_VAR, api_key)
    api_key = os.environ.get('OPENAI_API_KEY', api_key)
    args.openai_api_key = api_key
    
    # Handle performance optimization settings
    args.enable_performance_optimizations = not args.disable_performance_optimizations
    
    kwargs = {k: v for (k, v) in vars(args).items() if v is not None}
    progress = ProgressHooks()
    
    # Show performance info if verbose
    if args.verbose and args.enable_performance_optimizations:
        from .performance import get_hardware_info, create_performance_config
        hardware = get_hardware_info()
        perf_config = create_performance_config(hardware)
        print(f"Performance optimizations enabled:")
        print(f"  Hardware: {hardware['cpu_count']} CPUs, {hardware['memory_available_mb']:.0f}MB RAM")
        print(f"  Max concurrent LLM calls: {perf_config.max_concurrent_llm}")
        print(f"  Parallel processing: {'Enabled' if perf_config.enable_parallel_processing else 'Disabled'}")
    
    # Check if URL is a playlist
    if is_playlist_url(args.video_url):
        if args.verbose:
            print(f"Detected playlist URL: {args.video_url}")
        # Process playlist
        result = process_playlist(progress, args.video_url, **{k: v for k, v in kwargs.items() if k != 'video_url'})
        progress.close()
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"Playlist processing complete!")
        print(f"Playlist: '{result.playlist_title}'")
        print(f"Total videos: {result.total_videos}")
        print(f"Successful: {len(result.successful_videos)}")
        print(f"Failed: {len(result.failed_videos)}")
        
        if result.failed_videos:
            print(f"\nFailed videos:")
            for video_url, error in result.failed_videos:
                print(f"  - {video_url}: {error}")
        
        print(f"\nOutput folder: {result.output_folder}")
        print(f"{'='*60}")
        
        # Try to open the output folder
        for opener in ['open', 'xdg-open']:
            if shutil.which(opener) is not None:
                os.execlp(opener, opener, result.output_folder)
                return
        if shutil.which('cmd') is not None:
            os.execlp('cmd', 'cmd', '/c', result.output_folder)
    else:
        # Process single video (existing behavior)
        result = process_video(progress, **kwargs)
        progress.close()
        filename = os.path.join(OUT_DIR, f'{result.video_id}.html')
        os.makedirs(OUT_DIR, exist_ok = True)
        with open(filename, 'wb') as out:
            out.write(result.summary.encode('utf-8'))
        for opener in ['open', 'xdg-open']:
            if shutil.which(opener) is not None:
                os.execlp(opener, opener, filename)
                return
        if shutil.which('cmd') is not None:
            os.execlp('cmd', 'cmd', '/c', filename)
        print(f'Unable to open the file automatically, the output was written to {filename}')
