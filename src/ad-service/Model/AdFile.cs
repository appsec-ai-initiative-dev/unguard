// <copyright company="Dynatrace LLC">
// Copyright 2023 Dynatrace LLC
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
// </copyright>
 
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using System.Linq;

namespace AdService.Model
{
    public class AdFile
    {
        public static string FileFolder = "adFolder";
        public string Name { get; set; }
        public DateTime CreationTime { get; set; }

        /// <summary>Creates a path with webRootPath and FileFolder and checks if it contains files.</summary>
        ///
        public static bool FolderIsEmpty(string webRootPath)
        {
            var filePath = Path.Combine(webRootPath, FileFolder);
            
            // Check if directory exists before attempting to read files
            if (!Directory.Exists(filePath))
            {
                return true;
            }
            
            try
            {
                // Use EnumerateFiles instead of GetFiles to avoid race conditions
                // and reduce memory usage for large directories
                return !Directory.EnumerateFiles(filePath).Any();
            }
            catch (IOException)
            {
                // If directory is temporarily locked, assume not empty to avoid breaking the page
                return false;
            }
            catch (UnauthorizedAccessException)
            {
                // If we don't have access, assume not empty
                return false;
            }
        }
        
        /// <summary>Create a list of current available files.</summary>
        ///
        public static List<AdFile> CreateList(string webRootPath)
        {
            var imageDirectory = Path.Combine(webRootPath, FileFolder);
            
            // Check if directory exists before attempting to read files
            if (!Directory.Exists(imageDirectory))
            {
                return new List<AdFile>();
            }
            
            try
            {
                var filePaths = Directory.GetFiles(imageDirectory);
                return CreateList(filePaths);
            }
            catch (IOException)
            {
                // If directory is temporarily locked, return empty list
                return new List<AdFile>();
            }
            catch (UnauthorizedAccessException)
            {
                // If we don't have access, return empty list
                return new List<AdFile>();
            }
        }

        /// <summary>Create a list of current available files.</summary>
        ///
        public static List<AdFile> CreateList(IEnumerable filePath)
        {
            return (
                from string file in filePath
                select new AdFile { Name = Path.GetFileName(file), CreationTime = File.GetCreationTime(file) }
            ).ToList();
        }
    }
}