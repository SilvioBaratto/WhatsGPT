import argparse
import torch
import os
from torch.distributed import init_process_group, destroy_process_group
from GPTGram import GramTrainer
from GPTGram.config import Config as cfg

class DdpContext:
    def __init__(self, use_ddp):
        self.use_ddp = use_ddp

    def ddp_setup(self):
        """
        Initializes the distributed data parallel (DDP) environment and sets the configuration parameters.

        This function is used to set up the environment for distributed training. It initializes the process 
        group with a specified backend, sets the CUDA device for the current process, adjusts the 
        gradient accumulation steps according to the number of processes, and sets a manual seed for random 
        number generation. It also allows TensorFloat32 (TF32) on matrix multiplication (matmul) and CuDNN 
        operations.

        The function relies on environment variables set externally, including 'WORLD_SIZE', 'LOCAL_RANK', 
        and 'RANK'. These are usually set by the utility launching the distributed job.

        Raises:
            AssertionError: If the gradient accumulation steps is not divisible evenly by the DDP world size.

        Side Effects:
            1. Initializes the DDP process group with a specific backend.
            2. Sets the CUDA device for the current process based on the LOCAL_RANK.
            3. Adjusts the number of gradient accumulation steps according to the DDP world size.
            4. Sets a random seed for reproducibility.
            5. Enables TensorFloat32 for matmul and CuDNN operations in the CUDA backend.
        """
        init_process_group(backend=cfg.ddp.backend)
        torch.cuda.set_device(int(os.environ["LOCAL_RANK"]))

        seed_offset = int(os.environ['RANK'])
        torch.manual_seed(1337 + seed_offset)
        torch.backends.cuda.matmul.allow_tf32 = True  # allow tf32 on matmul
        torch.backends.cudnn.allow_tf32 = True  # allow tf32 on cudnn

    def __enter__(self):
        if self.use_ddp:
            self.ddp_setup()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.use_ddp:
            destroy_process_group()


def main(args):
    with DdpContext(cfg.ddp.ddp) as ddp_context:
        trainer = GramTrainer(filepath='../dataset/', **vars(args))
        trainer.train()


def arg_parser():
    parser = argparse.ArgumentParser(description='GPT Configuration')
    # Add this line to your arg_parser function
    parser.add_argument('--block_size', type=int, default=1024, help='Block size')
    parser.add_argument('--vocab_size', type=int, default=50304, help='Vocabulary size')
    parser.add_argument('--n_layer', type=int, default=12, help='Number of layers')
    parser.add_argument('--n_head', type=int, default=12, help='Number of heads')
    parser.add_argument('--n_embd', type=int, default=768, help='Embedding size')
    parser.add_argument('--dropout', type=float, default=0.0, help='Dropout rate')
    parser.add_argument('--bias', type=bool, default=True, help='Use bias in Linears and LayerNorms')

    parser.add_argument('--out_dir', type=str, default='out', help='Output directory')
    parser.add_argument('--eval_interval', type=int, default=2000, help='Evaluation interval')
    parser.add_argument('--log_interval', type=int, default=10, help='Logging interval')
    parser.add_argument('--eval_iters', type=int, default=200, help='Number of iterations for evaluation')
    parser.add_argument('--eval_only', type=bool, default=False, help='Evaluate only')
    parser.add_argument('--always_save_checkpoint', type=bool, default=True, help='Always save checkpoint')
    parser.add_argument('--init_from', type=str, default='scratch', help='Initialize from')
    parser.add_argument('--wandb_log', type=bool, default=True, help='Use wandb for logging')
    parser.add_argument('--wandb_project', type=str, default='owt', help='Wandb project name')
    parser.add_argument('--wandb_run_name', type=str, default='gpt2', help='Wandb run name')

    parser.add_argument('--dataset', type=str, default='whatsdataset', help='Dataset name')
    parser.add_argument('--gradient_accumulation_steps', type=int, default=40, help='Gradient accumulation steps')
    parser.add_argument('--batch_size', type=int, default=12, help='Batch size')

    parser.add_argument('--learning_rate', type=float, default=6e-4, help='Learning rate')
    parser.add_argument('--max_iters', type=int, default=600000, help='Maximum iterations')
    parser.add_argument('--weight_decay', type=float, default=1e-1, help='Weight decay')
    parser.add_argument('--beta1', type=float, default=0.9, help='Beta 1')
    parser.add_argument('--beta2', type=float, default=0.95, help='Beta 2')
    parser.add_argument('--grad_clip', type=float, default=1.0, help='Gradient clip')

    parser.add_argument('--decay_lr', type=bool, default=True, help='Decay learning rate')
    parser.add_argument('--warmup_iters', type=int, default=2000, help='Warmup iterations')
    parser.add_argument('--lr_decay_iters', type=int, default=600000, help='Learning rate decay iterations')
    parser.add_argument('--min_lr', type=float, default=6e-5, help='Minimum learning rate')

    parser.add_argument('--backend', type=str, default='nccl', help='DDP backend')

    parser.add_argument('--use_cuda', type=bool, default=torch.cuda.is_available(), help='Use CUDA')
    parser.add_argument('--dtype', type=str, default='bfloat16', help='Data type')
    parser.add_argument('--compile', type=bool, default=True, help='Compile')

    parser.add_argument('--start', type=str, default='\n', help='Start token')
    parser.add_argument('--num_samples', type=int, default=10, help='Number of samples')
    parser.add_argument('--max_new_tokens', type=int, default=500, help='Maximum new tokens')
    parser.add_argument('--temperature', type=float, default=0.8, help='Temperature')
    parser.add_argument('--top_k', type=int, default=200, help='Top k')
    parser.add_argument('--seed', type=int, default=1337, help='Seed')

    parser.add_argument('--folder', type=str, default='models', help='Folder for models')
    parser.add_argument('--num_workers', type=int, default=4, help='Number of workers')

    args = parser.parse_args()

    return args

if __name__ == '__main__':
    args = arg_parser()
    main(args)