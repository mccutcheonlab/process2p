t0=getTime()

print("Running macro to split 2photon tiff into chunks");

argString = getArgument();
args = split(argString, "(, )");

filename = args[0];
outputDir = args[1];
proj = args[2];
framesPerChunk = args[3];
z = args[4];

print("File to be processed is", filename);
print("Using", proj, "projection");
print("Number of frames per chunk is", framesPerChunk);
print("Number of z planes is", z);

//open tiff (give label if possible)
run("Bio-Formats Importer", "open=" + filename + " color_mode=Default view=Hyperstack stack_order=XYCZT");
print((getTime() - t0) / 1000, "s : File opened.");

fileStub = File.nameWithoutExtension;
//saveDir = File.directory + File.separator + "chunks";
//File.makeDirectory(saveDir);

print("Total number of slices is", nSlices());

while(nSlices() % 3 > 0) {
	setSlice(nSlices());
	run("Delete Slice");
}

//make z project
zprojectString = "order=xyczt(default) channels=1 slices=" + z + " frames="+ nSlices()/z + " display=Grayscale";
run("Stack to Hyperstack...", zprojectString);
run("Z Project...", "projection=[Max Intensity] all");
print((getTime() - t0) / 1000, " : Z-projection complete.");

print("Number of frames after processing is", nSlices());

i=1;

while (nSlices() > framesPerChunk) {
	print(nSlices());
	range="1-" + framesPerChunk;
	run("Make Substack...", "slices=" + range + " delete");
	saveAs("Tiff", outputDir + File.separator + "0" + i + "_" + fileStub);
	close();
	i++;
}

saveAs("Tiff", outputDir + File.separator + "0" + i + "_" + fileStub);
print((getTime() - t0) / 1000, "s : All files saved.");
print("Saved file as", i, "chunks. Exiting.");

